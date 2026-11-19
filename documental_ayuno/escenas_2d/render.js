// Renderiza animacion.html -> segmentos MP4 (H.264, 1080x1920, 30fps) con Chromium + FFmpeg.
// Uso: node render.js <dirSalida> [workers=4]
const {chromium}=require('playwright');const {spawn}=require('child_process');const fs=require('fs');
const out=process.argv[2],W=+(process.argv[3]||4),FPS=30,TOTAL=90*FPS;
fs.mkdirSync(out,{recursive:true});
async function job(w){
  const a=Math.floor(TOTAL/W*w),b=Math.floor(TOTAL/W*(w+1));
  const br=await chromium.launch();const pg=await br.newPage({viewport:{width:1080,height:1920}});
  await pg.goto('file://'+__dirname+'/animacion.html');
  const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(FPS),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','medium','-crf','15','-pix_fmt','yuv420p','-r',String(FPS),'-g','30','-bf','2','-movflags','+faststart',`${out}/seg${w}.mp4`],{stdio:['pipe','inherit','inherit']});
  for(let n=a;n<b;n++){
    await pg.evaluate(t=>render(t),n/FPS);
    const buf=await pg.screenshot({type:'jpeg',quality:95});
    if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));
    if(n%150==0)console.log(`worker ${w}: frame ${n}/${b}`);
  }
  ff.stdin.end();await new Promise(r=>ff.on('close',r));await br.close();
}
Promise.all([...Array(W).keys()].map(job)).then(()=>console.log('RENDER OK')).catch(e=>{console.error(e);process.exit(1)});
