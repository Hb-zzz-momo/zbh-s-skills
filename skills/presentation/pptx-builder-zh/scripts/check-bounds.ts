import fs from "node:fs";
import path from "node:path";
function usage() { console.log("Usage: tsx check-bounds.ts --spec slide-spec.json --manifest build-manifest.json --output build-check.json"); }
function parse(argv: string[]) { const o: any = {}; for (let i=0;i<argv.length;i++) { if (argv[i] === "--help" || argv[i] === "-h") o.help=true; else if(argv[i].startsWith("--")){ if(!argv[i+1]) throw new Error(`Missing value for ${argv[i]}`); o[argv[i].slice(2)]=argv[++i]; } } return o; }
function countText(value: string) { return (value.match(/[\u3400-\u9fff]|[A-Za-z0-9]+/g) || []).length; }
function main() {
  const args=parse(process.argv.slice(2)); if(args.help){usage();return;} if(!args.spec||!args.manifest||!args.output){usage();throw new Error("--spec, --manifest and --output are required");}
  const spec=JSON.parse(fs.readFileSync(path.resolve(args.spec),"utf8")); const manifest=JSON.parse(fs.readFileSync(path.resolve(args.manifest),"utf8")); const width=manifest.slide_size.width; const height=manifest.slide_size.height; const issues:any[]=[];
  for(const el of manifest.elements){ if(el.x < 0 || el.y < 0 || el.w <= 0 || el.h <= 0 || el.x + el.w > width + 0.001 || el.y + el.h > height + 0.001) issues.push({severity:"ERROR",slide_id:el.slide_id,component:el.component,message:"element_out_of_bounds",box:{x:el.x,y:el.y,w:el.w,h:el.h}}); }
  for(const slide of spec.slides){ const budget=slide.text_budget || {}; const title=countText(slide.claim || slide.purpose || ""); const body=countText((slide.content_blocks||[]).map((x:any)=>x.content||x.label||x.value||"").join(" ")); if(budget.title && title > budget.title) issues.push({severity:"WARNING",slide_id:slide.slide_id,component:"title",message:"title_budget_exceeded",actual:title,limit:budget.title}); if(budget.body && body > budget.body) issues.push({severity:"WARNING",slide_id:slide.slide_id,component:"body",message:"body_budget_exceeded",actual:body,limit:budget.body}); }
  const result={status:issues.some(x=>x.severity==="ERROR")?"FAIL":issues.length?"CAUTION":"PASS",issues,checked_elements:manifest.elements.length,checked_slides:spec.slides.length}; fs.mkdirSync(path.dirname(path.resolve(args.output)),{recursive:true}); fs.writeFileSync(path.resolve(args.output),JSON.stringify(result,null,2),"utf8"); console.log(JSON.stringify(result)); if(result.status === "FAIL") process.exitCode=2;
}
try{main();}catch(error:any){console.error(`ERROR: ${error.message}`);process.exitCode=1;}

