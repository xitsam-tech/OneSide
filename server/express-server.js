import express from 'express';
import cors from 'cors';
import fetch from 'node-fetch';

const app = express();
app.use(cors());
app.use(express.json({ limit: '1mb' }));

app.get('/api/health', (req,res)=>{
  res.json({ ok:true, ts: Date.now(), hasKey: !!process.env.OPENAI_API_KEY });
});

app.post('/api/translate', async (req,res)=>{
  try{
    if(!process.env.OPENAI_API_KEY){
      return res.status(501).json({ error: 'OPENAI_API_KEY not configured' });
    }
    const { text, to='en', model } = req.body || {};
    if(!text) return res.status(400).json({ error:'Missing text' });
    const useModel = model || process.env.OPENAI_MODEL || 'gpt-4o-mini';
    const prompt = `Übersetze präzise ins ${to}. Zahlen/Währung beibehalten. Nur Übersetzung.`;
    const r = await fetch('https://api.openai.com/v1/chat/completions', {
      method:'POST',
      headers:{ 'Authorization':`Bearer ${process.env.OPENAI_API_KEY}`, 'Content-Type':'application/json' },
      body: JSON.stringify({ model:useModel, temperature:0.2, messages:[
        { role:'system', content: prompt },
        { role:'user', content: String(text).slice(0,8000) }
      ]})
    });
    const j = await r.json();
    if(!r.ok) return res.status(502).json(j);
    res.json({ text: j.choices?.[0]?.message?.content?.trim()||'' });
  }catch(e){ res.status(500).json({ error:String(e) }); }
});

function zigZag(closes, threshold=0.04){
  const pts=[]; let dir=0; let last=closes[0]; let lastIdx=0;
  for(let i=1;i<closes.length;i++){
    const p=closes[i]; const chg=(p-last)/last;
    if(dir>=0 && chg<=-threshold){ pts.push({i:lastIdx, price:last}); dir=-1; last=p; lastIdx=i; }
    else if(dir<=0 && chg>=threshold){ pts.push({i:lastIdx, price:last}); dir=1; last=p; lastIdx=i; }
    if(Math.abs(chg)>threshold){ last=p; lastIdx=i; }
  }
  pts.push({i:closes.length-1, price:closes[closes.length-1]});
  return pts.slice(0, 12);
}
function fibLevels(candles){
  let hi=-Infinity, lo=Infinity;
  for(const c of candles){ hi=Math.max(hi, c[2]); lo=Math.min(lo, c[3]); }
  if(!isFinite(hi)||!isFinite(lo)) return null;
  return { hi, lo };
}
app.post('/api/analyze-chart', async (req,res)=>{
  try{
    let { candles, want } = req.body || {};
    if(!Array.isArray(candles) || candles.length<5){
      return res.status(400).json({ error:'Invalid candles' });
    }
    candles = candles.slice(-2000);
    const closes = candles.map(c=>c[4]);
    const resp = { ok:true };
    if(!want || want.fib) resp.fib = fibLevels(candles);
    if(!want || want.waves) resp.waves = zigZag(closes);
    res.json(resp);
  }catch(e){ res.status(500).json({ error:String(e) }); }
});

const PORT = process.env.PORT || 8787;
app.listen(PORT, ()=> console.log('Server on http://localhost:'+PORT));
