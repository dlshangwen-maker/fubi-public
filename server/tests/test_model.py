"""模型调用层测试：假模型、OpenAI 兼容接口、Anthropic 接口（用本机起的假服务器模拟）、格式不对时重试、额度上限、连不上时的报错。
运行：cd server && python3 -m unittest discover -s tests"""
import os,sys,json,threading,unittest,tempfile
from http.server import BaseHTTPRequestHandler,HTTPServer
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['FUBI_DATA']=tempfile.mkdtemp(prefix='fubi_test_')
import config,db,model,tasks

REPLIES=[]   # 假服务器依次返回的内容
SEEN=[]
class Fake(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        SEEN.append((self.path,dict(self.headers),body))
        txt=REPLIES.pop(0) if REPLIES else '{"ok": true}'
        if txt=='<500>': self.send_response(503); self.end_headers(); self.wfile.write(b'busy'); return
        if txt=='<LENGTH>': r={'choices':[{'message':{'content':'{"类型":"读过的","回答":"半截'},'finish_reason':'length'}]}
        elif txt=='<EMPTY>': r={'choices':[{'message':{'content':''},'finish_reason':'stop'}]}
        elif self.path.endswith('/chat/completions'): r={'choices':[{'message':{'content':txt},'finish_reason':'stop'}]}
        else: r={'content':[{'type':'text','text':txt}]}
        b=json.dumps(r).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(b)
srv=HTTPServer(('127.0.0.1',0),Fake); threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_port}'
def cfg(p,**k): return {'provider':p,'base_url':URL+('/v1' if p=='openai' else ''),'api_key':'sk-test','name':'test-model','timeout':5,'daily_calls':100,'book_calls':100,**k}

class T(unittest.TestCase):
    def setUp(self): REPLIES.clear(); SEEN.clear()
    def test_mock_uses_existing_data(self):
        out=model.call('cards_novel',{'chapter':1,'units':['1.1'],'done_dir':os.path.join(config.ROOT,'生成','猎犬')},cfg=dict(cfg('mock'),provider='mock'))
        self.assertIn('1.1',out); self.assertIn('华生',out['1.1']['入门']['白话'])
    def test_mock_placeholder_when_no_data(self):
        out=model.call('cards_novel',{'chapter':9,'units':['9.1','9.4']},cfg=dict(cfg('mock'),provider='mock'))
        self.assertEqual(set(out),{'9.1','9.4'}); self.assertIn('假模型',out['9.1']['入门']['白话'])
    def test_openai_compatible(self):
        REPLIES.append('```json\n{"类型":"书外","回答":"这是背景知识。"}\n```')
        out=model.call('ask',{'书名':'测试书','POS':'1.3'},cfg=cfg('openai'))
        self.assertEqual(out['类型'],'书外')
        path,h,body=SEEN[0]; self.assertEqual(path,'/v1/chat/completions'); self.assertEqual(h['Authorization'],'Bearer sk-test'); self.assertEqual(body['model'],'test-model')
        self.assertEqual(body['messages'][0]['role'],'system'); self.assertIn('测试书',body['messages'][1]['content'])
    def test_anthropic(self):
        REPLIES.append('好的：{"类型":"读过的","回答":"见 1.2。","引用":["1.2"]}')
        out=model.call('ask',{'书名':'测试书','POS':'1.3'},cfg=cfg('anthropic'))
        self.assertEqual(out['引用'],['1.2'])
        path,h,body=SEEN[0]; self.assertEqual(path,'/v1/messages'); self.assertEqual(h['X-Api-Key'],'sk-test'); self.assertIn('system',body)
    def test_retry_on_bad_format(self):
        REPLIES.extend(['不是 JSON','{"类型":"乱写","回答":"x"}'])
        with self.assertRaises(model.BadOutput): model.call('ask',{},cfg=cfg('openai'))
        self.assertEqual(len(SEEN),2); self.assertIn('上一次的输出有这些问题',SEEN[1][2]['messages'][1]['content'])
        REPLIES.extend(['不是 JSON','{"类型":"后面有","回答":"后面会读到。"}'])
        self.assertEqual(model.call('ask',{},cfg=cfg('openai'))['类型'],'后面有')
    def test_validation_cards(self):
        REPLIES.extend(['{"2.1":{"入门":{"白话":"a","展开":"b","前置":""}}}']*2)
        with self.assertRaises(model.BadOutput) as e: model.call('cards_novel',{'chapter':2,'units':['2.1','2.5']},cfg=cfg('openai'))
        self.assertIn('少了单元 2.5',str(e.exception))
    def test_request_sets_max_tokens_and_json_mode(self):
        REPLIES.append('{"类型":"书外","回答":"x"}'); model.call('ask',{'书名':'书','POS':'1.1'},cfg=cfg('openai',max_tokens=4096))
        body=SEEN[0][2]; self.assertEqual(body['max_tokens'],4096,'DeepSeek 不设上限会截断长回答'); self.assertEqual(body['response_format'],{'type':'json_object'})
    def test_thinking_switch_is_sent_only_when_configured(self):
        REPLIES.append('{"类型":"书外","回答":"x"}'); model.call('ask',{'书名':'书','POS':'1.1'},cfg=cfg('openai'))
        self.assertNotIn('thinking',SEEN[0][2],'没配置就不发，用厂商默认')
        SEEN.clear(); REPLIES.append('{"类型":"书外","回答":"x"}'); model.call('ask',{'书名':'书','POS':'1.1'},cfg=cfg('openai',thinking='disabled'))
        self.assertEqual(SEEN[0][2]['thinking'],{'type':'disabled'})
        SEEN.clear(); REPLIES.append('{"类型":"书外","回答":"x"}'); model.call('ask',{'书名':'书','POS':'1.1'},cfg=cfg('openai',thinking='乱填'))
        self.assertNotIn('thinking',SEEN[0][2],'不认识的值不发，免得被厂商拒绝')
    def test_effort_sent_only_when_thinking_not_disabled(self):
        for kw,expect in (({'effort':'low'},'low'),({'effort':'low','thinking':'enabled'},'low'),({'effort':'low','thinking':'disabled'},None),({'effort':'乱填'},None),({},None)):
            SEEN.clear(); REPLIES.append('{"类型":"书外","回答":"x"}'); model.call('ask',{'书名':'书','POS':'1.1'},cfg=cfg('openai',**kw))
            self.assertEqual(SEEN[0][2].get('reasoning_effort'),expect,kw)
    def test_describe_for_admin_page(self):
        d=model.describe(cfg('openai',base_url='https://api.deepseek.com',name='deepseek-flash',thinking='disabled'))
        self.assertEqual(d['line'],'DeepSeek · deepseek-flash（DeepSeek-V4.1-Flash-1017） · 思考模式：已关闭')
        self.assertIn('已开启，强度 low',model.describe(cfg('openai',base_url='https://api.deepseek.com',name='deepseek-flash',thinking='enabled',effort='low'))['line'])
        self.assertIn('厂商默认',model.describe(cfg('openai',base_url='https://api.deepseek.com',name='deepseek-flash'))['line'],'没配置时不替厂商猜默认值')
        self.assertIn('Anthropic',model.describe(cfg('anthropic',base_url='',name='claude-x'))['line'])
        self.assertIn('api.example.com',model.describe(cfg('openai',base_url='https://api.example.com/v1',name='m'))['line'],'认不出的厂商显示域名')
        self.assertIn('假模型',model.describe(dict(cfg('mock'),provider='mock'))['line'])
    def test_health_shows_raw_reply_when_not_json(self):
        REPLIES.extend(['好的，我来回答：ok是真的']*3)
        h=model.health(cfg('openai')); self.assertFalse(h['ok']); self.assertIn('不是合法 JSON',h['msg']); self.assertIn('好的，我来回答',h['msg'],'要带上模型原文，才能判断是谁的问题'); self.assertEqual(len(SEEN),3,'最多试三次')
    def test_health_retries_once_on_stray_token(self):
        REPLIES.extend(['{"ok":<|endoftext|>true}','{"ok": true}'])   # 线上真实出现过的坏回答
        h=model.health(cfg('openai')); self.assertTrue(h['ok']); self.assertIn('已自动重试',h['msg']); self.assertEqual(len(SEEN),2)
    def test_health_retry_tells_model_what_was_wrong_and_tries_three_times(self):
        """11-04 线上连续两次都夹进 <|endoftext|>：原来重试发的是一模一样的提示，现在要把问题告诉模型，并多给一次机会"""
        REPLIES.extend(['{"ok":<|endoftext|>true}','{"ok":<|endoftext|>true}','{"ok": true}'])
        h=model.health(cfg('openai')); self.assertTrue(h['ok'],h); self.assertEqual(len(SEEN),3); self.assertIn('已自动重试 2 次',h['msg'])
        self.assertNotIn('内部符号',SEEN[0][2]['messages'][1]['content']); self.assertIn('内部符号',SEEN[1][2]['messages'][1]['content'],'重试时告诉模型上一次错在哪'); self.assertIn('<|endoftext|>',SEEN[1][2]['messages'][1]['content'])
    def test_health_fails_after_three_stray_replies_and_shows_raw(self):
        SEEN.clear(); REPLIES.extend(['{"ok":<|endoftext|>true}']*3)
        h=model.health(cfg('openai')); self.assertFalse(h['ok']); self.assertEqual(len(SEEN),3); self.assertIn('连续 3 次',h['msg']); self.assertIn('内部符号',h['msg']); self.assertIn('<|endoftext|>',h['msg'],'带上模型原文')
    def test_health_wrong_content_vs_unreachable(self):
        REPLIES.extend(['{"ok": false}']*3); h=model.health(cfg('openai')); self.assertFalse(h['ok']); self.assertIn('回答不对',h['msg'])
        h=model.health(dict(cfg('openai'),base_url='http://127.0.0.1:1/v1',timeout=2)); self.assertFalse(h['ok']); self.assertIn('连不上',h['msg'])
        REPLIES.append('{"ok": true}'); self.assertTrue(model.health(cfg('openai'))['ok'])
    def test_stray_internal_token_inside_text_is_rejected_and_retried(self):
        # JSON 本身合法、符号夹在某句话里——这种最危险，会原样存进读者看到的解释
        REPLIES.extend(['{"类型":"书外","回答":"这是背景知识<|endoftext|>。"}','{"类型":"书外","回答":"这是背景知识。"}'])
        out=model.call('ask',{'书名':'书','POS':'1.1'},cfg=cfg('openai'))
        self.assertEqual(out['回答'],'这是背景知识。'); self.assertEqual(len(SEEN),2)
        self.assertIn('内部符号',SEEN[1][2]['messages'][1]['content'],'重试时要把原因告诉模型')
        SEEN.clear(); REPLIES.extend(['{"类型":"书外","回答":"x<|im_end|>"}']*2)
        with self.assertRaises(model.BadOutput) as e: model.call('ask',{'书名':'书','POS':'1.1'},cfg=cfg('openai'))
        self.assertIn('内部符号',str(e.exception),'两次都有就失败，不存')
    def test_find_stray_does_not_flag_normal_text(self):
        for ok in ('a < b 且 c > d','集合 {x|x>0}','|x| < 1','<p>标签</p>','a<|b'): self.assertEqual(model.find_stray(ok),[],ok)
        self.assertEqual(model.find_stray('x<|endoftext|>y<|im_end|>'),['<|endoftext|>','<|im_end|>'])
    def test_default_limits(self):
        self.assertEqual(config.MODEL['max_tokens'],32000); self.assertEqual(config.MODEL['timeout'],300)
    def test_truncated_answer_is_not_retried(self):
        REPLIES.extend(['<LENGTH>']*3)
        with self.assertRaises(model.TruncatedOutput) as e: model.call('ask',{},cfg=cfg('openai'))
        self.assertEqual(len(SEEN),1,'截断后再发同样的请求没用，只发一次'); self.assertIn('截断',str(e.exception))
    def test_empty_content_is_an_error_not_bad_format(self):
        REPLIES.append('<EMPTY>')
        with self.assertRaises(model.ModelError) as e: model.call('ask',{},cfg=cfg('openai'))
        self.assertIn('空内容',str(e.exception))
    def test_transient_error_retried_once_then_succeeds(self):
        os.environ['FUBI_MODEL_RETRY_WAIT']='0'
        try:
            REPLIES.extend(['<500>','{"类型":"书外","回答":"重试后成功"}'])
            self.assertEqual(model.call('ask',{},cfg=cfg('openai'))['回答'],'重试后成功'); self.assertEqual(len(SEEN),2)
            SEEN.clear(); REPLIES.extend(['<500>','<500>','<500>'])
            with self.assertRaises(model.Transient): model.call('ask',{},cfg=cfg('openai'))
            self.assertEqual(len(SEEN),2,'只重试一次')
        finally: os.environ.pop('FUBI_MODEL_RETRY_WAIT',None)
    def test_server_error_is_reported(self):
        os.environ['FUBI_MODEL_RETRY_WAIT']='0'   # 调用层会自动再试一次，所以要连续两次 503 才会报错
        try:
            REPLIES.extend(['<500>','<500>'])
            with self.assertRaises(model.ModelError) as e: model.call('ask',{},cfg=cfg('openai'))
            self.assertIn('暂时不可用',str(e.exception))
        finally: os.environ.pop('FUBI_MODEL_RETRY_WAIT',None)
    def test_unreachable(self):
        with self.assertRaises(model.ModelError) as e: model.call('ask',{},cfg=dict(cfg('openai'),base_url='http://127.0.0.1:1/v1',timeout=2))
        self.assertIn('连不上',str(e.exception))
    def test_missing_key(self):
        with self.assertRaises(model.ModelError) as e: model.call('ask',{},cfg=dict(cfg('openai'),api_key=''))
        self.assertIn('密钥',str(e.exception))
    def test_quota(self):
        old=dict(config.MODEL); config.MODEL.update(cfg('openai',daily_calls=1))
        try:
            REPLIES.append('{"类型":"书外","回答":"x"}'); model.call('ask',{},book='q')
            with self.assertRaises(model.QuotaExceeded): model.call('ask',{},book='q')
        finally: config.MODEL.clear(); config.MODEL.update(old)
    def test_calls_are_logged(self):
        n=db.one('select count(*) from model_calls')[0]
        REPLIES.append('{"类型":"书外","回答":"x"}'); model.call('ask',{},book='log',cfg=cfg('openai'))
        self.assertEqual(db.one('select count(*) from model_calls')[0],n+1)
    def test_health(self):
        REPLIES.append('{"ok": true}'); self.assertTrue(model.health(cfg('openai'))['ok'])
        self.assertFalse(model.health(dict(cfg('openai'),base_url='http://127.0.0.1:1/v1',timeout=2))['ok'])
    def test_every_prompt_file_exists(self):
        for k,t in tasks.TASKS.items():
            s,u=t.render({'书名':'X','POS':'1.1'}); self.assertTrue(len(u)>100,k)
if __name__=='__main__': unittest.main()
