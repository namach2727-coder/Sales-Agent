"""Payexa lifecycle using the existing commerce ownership and activation boundary."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.commerce.service import CommerceService, CommerceConflict, CommerceNotFound, now_utc
from app.commerce.payexa_provider import PayexaCreateUnknown, PayexaError
from app.models import ManualPayment, SubscriptionOrder, SaasPlan


class PayexaService(CommerceService):
    def create(self, principal, order_public_id, *, provider, callback_base_url):
        tenant, store = self.customer_scope(principal)
        order = self.session.scalar(select(SubscriptionOrder).where(
            SubscriptionOrder.public_id == order_public_id,
            SubscriptionOrder.tenant_id == tenant.id,
            SubscriptionOrder.store_id == store.id,
            SubscriptionOrder.user_id == principal.user_id,
        ).with_for_update())
        if order is None:
            raise CommerceNotFound('order not found')
        existing = self.session.scalar(select(ManualPayment).where(ManualPayment.order_id == order.id).with_for_update())
        if existing:
            if existing.provider != 'payexa':
                raise CommerceConflict('order already uses another payment provider')
            return existing
        required = ('plan_code_snapshot', 'plan_name_snapshot', 'product_family_snapshot', 'duration_days_snapshot', 'instagram_account_limit_snapshot', 'automation_limit_snapshot', 'ai_reply_limit_snapshot')
        if order.status != 'pending' or order.price_amount <= 0 or order.currency != 'IRR' or any(getattr(order, name) is None for name in required):
            raise CommerceConflict('order commercial snapshot is not payable')
        payment = ManualPayment(tenant_id=tenant.id, store_id=store.id, user_id=principal.user_id, order_id=order.id, provider='payexa', status='pending', amount=order.price_amount, currency=order.currency, provider_operation_state='CREATE_IN_FLIGHT')
        self.session.add(payment)
        try:
            self.session.flush()
            self._audit(tenant.id, store.id, principal.user_id, 'payment.payexa_create_started', 'payment', payment.public_id, {})
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            existing = self.session.scalar(select(ManualPayment).where(ManualPayment.order_id == order.id))
            if existing is None or existing.provider != 'payexa':
                raise CommerceConflict('payment creation conflict') from None
            return existing
        try:
            result = provider.create_transaction(amount=payment.amount, callback_url=f'{callback_base_url.rstrip("/")}/api/v1/payments/payexa/callback/{payment.public_id}', order_ref=payment.public_id)
        except (PayexaCreateUnknown, PayexaError) as error:
            locked = self._lock_payment(payment.public_id)
            locked.provider_operation_state = 'CREATE_UNKNOWN' if isinstance(error, PayexaCreateUnknown) else 'FAILED'
            locked.revision += 1
            self.session.commit()
            return locked
        locked = self._lock_payment(payment.public_id)
        locked.provider_transaction_id = result.transaction_id
        locked.provider_authority = result.authority
        locked.provider_verification_token = result.verification_token
        locked.provider_payment_url = result.payment_url
        locked.provider_status = 'PENDING'
        locked.provider_created_at = now_utc()
        locked.provider_operation_state = 'CREATED'
        locked.revision += 1
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            locked = self._lock_payment(payment.public_id)
            locked.provider_operation_state = 'CREATE_UNKNOWN'
            self.session.commit()
        return locked

    def verify(self, payment_public_id, *, provider):
        payment = self._lock_payment(payment_public_id)
        if payment.provider != 'payexa':
            raise CommerceNotFound('Payexa payment not found')
        if payment.provider_operation_state in ('PAID', 'FAILED', 'RECONCILIATION_REQUIRED'):
            return payment
        if not payment.provider_transaction_id or not payment.provider_verification_token:
            raise CommerceConflict('Payexa identity is unavailable')
        # Hold the row lock through verification and local commit so concurrent
        # callbacks cannot race a 200 response against a 201 replay.
        payment.provider_operation_state = 'VERIFY_PENDING'
        try:
            result = provider.verify_transaction(order_id=payment.provider_transaction_id, token=payment.provider_verification_token)
        except PayexaError:
            payment.revision += 1
            self.session.commit()
            return payment
        payment.provider_status = result.status
        payment.revision += 1
        if result.http_status == 201:
            payment.provider_operation_state = 'RECONCILIATION_REQUIRED'
        elif result.http_status in (400, 404):
            payment.provider_operation_state = 'FAILED'
        elif result.http_status == 200 and result.status == 'SUCCESS':
            order = self.session.scalar(select(SubscriptionOrder).where(SubscriptionOrder.id == payment.order_id).with_for_update())
            plan = self.session.get(SaasPlan, order.plan_id) if order else None
            if order is None or plan is None or order.status != 'pending' or payment.status != 'pending' or order.tenant_id != payment.tenant_id or order.store_id != payment.store_id or order.user_id != payment.user_id or order.price_amount != payment.amount or order.currency != payment.currency or order.currency != 'IRR' or order.plan_code_snapshot is None:
                payment.provider_operation_state = 'RECONCILIATION_REQUIRED'
            else:
                payment.status = 'approved'
                payment.provider_operation_state = 'PAID'
                payment.approved_at = now_utc()
                order.status = 'paid'
                self._activate_paid_subscription(order, plan, payment)
        self._audit(payment.tenant_id, payment.store_id, None, 'payment.payexa_verify_result', 'payment', payment.public_id, {'operation_state': payment.provider_operation_state})
        self.session.commit()
        return payment
