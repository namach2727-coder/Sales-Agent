import unittest
import os
from unittest.mock import AsyncMock, patch
from cryptography.fernet import Fernet
from experiments.telegram_bot_builder.api_actions import seal_call, ApiActionError
from experiments.telegram_bot_builder.vault import TokenVault
from experiments.telegram_bot_builder.reply_runtime import process_reply


class Cursor:
    def __init__(self, value): self.value=value
    def fetchone(self): return self.value
    def fetchall(self): return self.value


class RuleDB:
    def __init__(self,key):
        self.events=[];self.paused=False;self.used=0;self.lock=True
        self.rules=[{'id':'api-rule','keyword':'قیمت','match_mode':'exact','response_text':'Service unavailable','enabled':True,'priority':0,'action_type':'api',
            'api_request_ciphertext':seal_call({'url':'https://api.example.com/a','response_path':'answer'},key)},
            {'id':'text-rule','keyword':'آدرس','match_mode':'contains','response_text':'Address','enabled':True,'priority':1,'action_type':'text','api_request_ciphertext':None}]
    def commit(self): self.events.append('commit')
    def execute(self,sql,args=()):
        self.events.append((sql,args))
        if 'SELECT version FROM' in sql:return Cursor({'version':'0003_rule_api_calls'})
        if 'FROM telbot.configuration_versions' in sql:return Cursor({'id':'config','greeting':'Hello','fallback_reply':'Fallback'})
        if 'FROM telbot.reply_rules' in sql:return Cursor(self.rules)
        if 'INSERT INTO telbot.chat_sessions' in sql:return Cursor({'id':'session','status':'paused' if self.paused else 'open'})
        if 'INSERT INTO telbot.outbound_messages' in sql:return Cursor({'id':'outbound'})
        if 'pg_try_advisory' in sql:return Cursor({'acquired':self.lock})
        if 'count(*) AS n' in sql:return Cursor({'n':self.used})
        return Cursor(None)


class RuleRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.key=Fernet.generate_key().decode();self.db=RuleDB(self.key)
        self.bot={'tenant_id':'tenant','id':'bot','credential_ciphertext':TokenVault(self.key).encrypt('42:synthetic')}
        self.event={'_bot_id':42,'message':{'text':'قیمت','from':{'id':123,'is_bot':False},'chat':{'id':123,'type':'private'}}}
        self.env=patch.dict(os.environ,{'TELBOT_ENV':'uat','TELBOT_REPLIES_ENABLED':'true','TELBOT_EXTERNAL_API_ENABLED':'true','TELBOT_TOKEN_FERNET_KEY':self.key});self.env.start()
    async def asyncTearDown(self): self.env.stop()
    async def test_committed_attempt_before_api_then_result_before_send(self):
        async def call(value,text):
            self.assertEqual(self.db.events[-1],'commit')
            self.assertTrue(any(isinstance(e,tuple) and 'INSERT INTO telbot.outbound_messages' in e[0] for e in self.db.events))
            return 'API price'
        async def sent(token,payload):
            self.assertEqual(payload['text'],'API price');self.assertEqual(self.db.events[-1],'commit');return 7,None
        with patch('experiments.telegram_bot_builder.reply_runtime.invoke_api',side_effect=call) as api,patch('experiments.telegram_bot_builder.reply_runtime.send_text',side_effect=sent):
            await process_reply(self.db,self.bot,self.event,'inbound');self.assertEqual(api.call_count,1)
    async def test_failed_api_uses_configured_fallback_without_raw_error(self):
        with patch('experiments.telegram_bot_builder.reply_runtime.invoke_api',new_callable=AsyncMock,side_effect=ApiActionError('api_timeout')) as api,patch('experiments.telegram_bot_builder.reply_runtime.send_text',new_callable=AsyncMock,return_value=(7,None)) as sender:
            await process_reply(self.db,self.bot,self.event,'inbound')
            self.assertEqual(sender.call_args.args[1]['text'],'Service unavailable');self.assertEqual(api.call_count,1)
            self.assertTrue(any(isinstance(e,tuple) and 'UPDATE telbot.outbound_messages SET delivery_status' in e[0] and e[1][2]=='api_timeout' for e in self.db.events))
    async def test_api_off_paused_disabled_start_and_budget_do_not_call_api(self):
        for mode in ['off','paused','disabled','start','rate','busy','text']:
            self.db=RuleDB(self.key);self.event['message']['text']='قیمت'
            if mode=='paused':self.db.paused=True
            if mode=='disabled':self.db.rules[0]['enabled']=False
            if mode=='start':self.event['message']['text']='/start campaign'
            if mode=='text':self.event['message']['text']='آدرس فروشگاه'
            if mode=='rate':self.db.used=20
            if mode=='busy':self.db.lock=False
            with self.subTest(mode=mode),patch.dict(os.environ,{'TELBOT_EXTERNAL_API_ENABLED':'false' if mode=='off' else 'true'}),patch('experiments.telegram_bot_builder.reply_runtime.invoke_api',new_callable=AsyncMock) as api,patch('experiments.telegram_bot_builder.reply_runtime.send_text',new_callable=AsyncMock,return_value=(7,None)):
                await process_reply(self.db,self.bot,self.event,'inbound');api.assert_not_called()
