"""Pure service-order state machine. No network, storage, Telegram or AI.

External receipts are accepted only by the trusted-adapter method, not customer
input. This prototype requires durable operation storage and real adapters
before it may run a live checkout/provisioning workflow.
"""
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, SecretStr, StrictBool, StrictInt, ValidationError


class FlowError(ValueError):
    """Categorical errors only: never include provider bodies or credentials."""


class Plan(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    id: str = Field(min_length=1,max_length=64)
    title: str = Field(min_length=1,max_length=120)
    amount: StrictInt = Field(gt=0,le=10**12)
    currency: str = Field(pattern='^[A-Z]{3}$')


class CheckoutReceipt(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    order_id: str = Field(min_length=1,max_length=100)
    payment_ref: str = Field(min_length=1,max_length=120)
    checkout_url: str = Field(min_length=8,max_length=2048)


class PaymentReceipt(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    order_id: str
    payment_ref: str
    paid: StrictBool
    amount: StrictInt
    currency: str


class AccountReceipt(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    order_id: str
    username: SecretStr = Field(min_length=1,max_length=120)
    password: SecretStr = Field(min_length=1,max_length=512)
    config_text: SecretStr = Field(min_length=1,max_length=16384)


@dataclass(frozen=True)
class Order:
    id: str
    plan_id: str
    amount: int
    currency: str


@dataclass(frozen=True)
class ExternalCall:
    kind: Literal['checkout','verify_payment','provision']
    operation_id: str
    order: Order
    # Supply this key to a provider with an explicit idempotency contract.
    @property
    def idempotency_key(self):return self.operation_id


@dataclass
class ServiceFlow:
    tenant_id: UUID
    bot_id: UUID
    customer_key: str = field(repr=False)
    plans: tuple[Plan,...]
    checkout_hosts: tuple[str,...]
    run_id: UUID = field(default_factory=uuid4)
    phase: str = field(default='select_plan',init=False)
    order: Order | None = field(default=None,init=False)
    pending: ExternalCall | None = field(default=None,init=False)
    payment_ref: str | None = field(default=None,init=False,repr=False)
    checkout_url: str | None = field(default=None,init=False,repr=False)
    payment_verified: bool = field(default=False,init=False)
    account: AccountReceipt | None = field(default=None,init=False,repr=False)
    events: list[str] = field(default_factory=list,init=False)
    _consumed: set[str] = field(default_factory=set,init=False,repr=False)
    _checks: int = field(default=0,init=False,repr=False)

    def __post_init__(self):
        if not self.customer_key or not 1<=len(self.plans)<=12 or not self.checkout_hosts:
            raise FlowError('invalid_contract')
        if len({p.id for p in self.plans})!=len(self.plans):raise FlowError('duplicate_plan')
        # Immutable prices copied from the trusted versioned configuration.
        self.plans=tuple(Plan.model_validate(p.model_dump()) for p in self.plans)

    def _key(self,label):
        scope=f'{self.tenant_id}:{self.bot_id}:{self.customer_key}:{self.run_id}:service-v1:{label}'
        return sha256(scope.encode()).hexdigest()

    def _issue(self,kind):
        if kind=='provision' and not self.payment_verified:raise FlowError('payment_required')
        suffix=str(self._checks) if kind=='verify_payment' else '1'
        self.pending=ExternalCall(kind,self._key(kind+':'+suffix),self.order)
        self.phase=kind+'_pending';self.events.append(kind+'_requested')
        return self.pending

    def choose_plan(self,plan_id):
        if self.phase!='select_plan':return None
        plan=next((p for p in self.plans if p.id==plan_id),None)
        if not plan:raise FlowError('unknown_plan')
        self.order=Order('ord_'+self._key('order')[:24],plan.id,plan.amount,plan.currency)
        self.events.append('order_created')
        return self._issue('checkout')

    def check_payment(self):
        if self.phase!='awaiting_payment':return None
        if self._checks>=10:
            self.phase='review_required';self.events.append('verification_limit');return None
        self._checks+=1
        return self._issue('verify_payment')

    def cancel(self):
        if self.phase not in ('select_plan','awaiting_payment'):return False
        self.phase='cancelled';self.events.append('cancelled');return True

    def accept_external(self,operation_id,payload):
        """Trusted provider-adapter boundary. Never expose as customer API input."""
        if operation_id in self._consumed:return None
        if not self.pending or operation_id!=self.pending.operation_id:raise FlowError('unexpected_operation')
        call=self.pending
        try:
            if call.kind=='checkout':
                receipt=CheckoutReceipt.model_validate(payload)
                url=urlsplit(receipt.checkout_url)
                if (receipt.order_id!=self.order.id or url.scheme!='https' or url.username or url.password
                    or url.hostname not in self.checkout_hosts or url.port not in (None,443) or url.fragment):
                    raise FlowError('invalid_checkout')
                self.payment_ref=receipt.payment_ref;self.checkout_url=receipt.checkout_url
                self.phase='awaiting_payment';self.events.append('checkout_ready')
            elif call.kind=='verify_payment':
                receipt=PaymentReceipt.model_validate(payload)
                if (receipt.order_id!=self.order.id or receipt.payment_ref!=self.payment_ref
                    or receipt.amount!=self.order.amount or receipt.currency!=self.order.currency):
                    raise FlowError('payment_mismatch')
                if not receipt.paid:
                    self.phase='awaiting_payment';self.events.append('payment_not_confirmed')
                else:
                    self.payment_verified=True;self.events.append('payment_verified')
            else:
                if not self.payment_verified:raise FlowError('payment_required')
                receipt=AccountReceipt.model_validate(payload)
                if receipt.order_id!=self.order.id:raise FlowError('account_order_mismatch')
                self.account=receipt;self.phase='delivered';self.events.append('account_ready')
        except (ValidationError,ValueError,TypeError) as exc:
            code=str(exc) if isinstance(exc,FlowError) else 'invalid_provider_result'
            self.phase='review_required';self.events.append(code)
            self._consumed.add(operation_id);self.pending=None
            raise FlowError(code) from None
        self._consumed.add(operation_id);self.pending=None
        if call.kind=='verify_payment' and self.payment_verified:return self._issue('provision')
        return None

    def transport_unknown(self,operation_id):
        if operation_id in self._consumed:return
        if not self.pending or self.pending.operation_id!=operation_id:raise FlowError('unexpected_operation')
        self._consumed.add(operation_id);self.pending=None;self.phase='review_required'
        self.events.append('external_outcome_unknown')


def run_demo(tenant_id,bot_id,customer_key,plan_id='basic',scenario='paid'):
    """Synthetic adapter only. Cannot execute network or real payment/account actions."""
    if scenario not in ('paid','pending','mismatch','timeout'):raise FlowError('unknown_demo')
    plans=(Plan(id='basic',title='پلن نمونهٔ ۱',amount=10000,currency='IRT'),
           Plan(id='plus',title='پلن نمونهٔ ۲',amount=20000,currency='IRT'))
    flow=ServiceFlow(tenant_id,bot_id,customer_key,plans,('checkout.example.com',))
    checkout=flow.choose_plan(plan_id)
    flow.accept_external(checkout.operation_id,{'order_id':flow.order.id,'payment_ref':'DEMO-PAYMENT',
        'checkout_url':'https://checkout.example.com/demo-only'})
    verify=flow.check_payment()
    try:
        provision=flow.accept_external(verify.operation_id,{'order_id':flow.order.id,'payment_ref':'DEMO-PAYMENT',
            'paid':scenario!='pending','amount':flow.order.amount+(1 if scenario=='mismatch' else 0),'currency':'IRT'})
        if provision:
            if scenario=='timeout':flow.transport_unknown(provision.operation_id)
            else:flow.accept_external(provision.operation_id,{'order_id':flow.order.id,'username':'DEMO-USER',
                'password':'DEMO-PASSWORD-NOT-VALID','config_text':'DEMO-CONFIG-NOT-A-VPN-CONNECTION'})
    except FlowError:
        pass
    labels={'order_created':'سفارش با مبلغ ثابت ساخته شد','checkout_requested':'درخواست لینک پرداخت از سرویس نمونه',
        'checkout_ready':'لینک پرداخت نمونه آماده شد','verify_payment_requested':'بررسی پرداخت از سرویس نمونه',
        'payment_verified':'شماره سفارش، مرجع، مبلغ و واحد پرداخت تطبیق داشت','payment_not_confirmed':'پرداخت هنوز تأیید نشده؛ صدور حساب انجام نمی‌شود',
        'payment_mismatch':'اطلاعات پرداخت مغایر است؛ صدور متوقف شد','provision_requested':'درخواست صدور حساب با شناسهٔ یکتای عملیات',
        'account_ready':'نام کاربری، رمز و کانفیگ نمونه آمادهٔ تحویل است',
        'external_outcome_unknown':'نتیجهٔ صدور نامشخص است؛ درخواست دوباره ارسال نمی‌شود'}
    return {'simulation':True,'live_actions':False,'phase':flow.phase,'amount':flow.order.amount,'currency':flow.order.currency,
        'checkout_url':flow.checkout_url,'steps':[labels[e] for e in flow.events],
        'demo_delivery':{'username':'DEMO-USER','password':'DEMO-PASSWORD-NOT-VALID',
          'config_text':'DEMO-CONFIG-NOT-A-VPN-CONNECTION'} if flow.account else None}
