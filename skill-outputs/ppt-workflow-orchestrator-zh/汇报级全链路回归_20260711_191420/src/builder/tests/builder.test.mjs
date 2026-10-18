import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, writeFile, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import JSZip from "jszip";

const root=path.resolve(import.meta.dirname,"..");
const design=`# Design\n\n\`\`\`presentation-theme\n${JSON.stringify({slide:{width:13.333,height:7.5,margin:.55},colors:{ink:"172033",muted:"5E6B7A",paper:"F7F4ED",surface:"FFFFFF",accent:"E05A47",accent2:"1B7F79",line:"D7D9DD"},fonts:{head:"Arial",body:"Arial",mono:"Consolas"},sizes:{hero:30,title:24,body:15,small:10,metric:28},radius:.12,gap:.28,layout_families:["chart-native","table","visual-image"],motif:"rail",forbidden_patterns:["screenshots"]})}\n\`\`\`\n`;
const common={section:"test",purpose:"test",audience_takeaway:"takeaway",claim:"claim",evidence_refs:["SRC"],dominant_asset:null,text_budget:{title:20,body:50,footer:10},source_footer:["SRC"],speaker_notes:"note",qa_checks:["check"]};

test("builder emits editable chart, table, images, SVG, notes and master", async()=>{
  const td=await mkdtemp(path.join(tmpdir(),"pptx-builder-")); const spec={deck:{title:"test",target_slides:4},slides:[
    {...common,slide_id:"S01",visual_type:"chart",layout_family:"chart-native",content_blocks:[{type:"chart",spec:"chart.json"}]},
    {...common,slide_id:"S02",visual_type:"table",layout_family:"table",content_blocks:[{type:"table",rows:[["A","B"],["1","2"]]}]},
    {...common,slide_id:"S03",visual_type:"image",layout_family:"visual-image",content_blocks:[{type:"image",path:"pixel.png",fit:"contain",alt:"pixel"}]},
    {...common,slide_id:"S04",visual_type:"svg",layout_family:"visual-image",content_blocks:[{type:"svg",path:"icon.svg",alt:"icon"}]}
  ]};
  await writeFile(path.join(td,"design.md"),design); await writeFile(path.join(td,"spec.json"),JSON.stringify(spec));
  await writeFile(path.join(td,"chart.json"),JSON.stringify({title:"data",chart_type:"column",categories:["A","B"],series:[{name:"S",values:[1,2]}],unit:"%",axis:{zero_baseline:true}}));
  await writeFile(path.join(td,"pixel.png"),Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlV6NwAAAAASUVORK5CYII=","base64"));
  await writeFile(path.join(td,"icon.svg"),`<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40" fill="#E05A47"/></svg>`);
  const out=path.join(td,"deck.pptx"); const cp=spawnSync(process.execPath,[path.join(root,"node_modules","tsx","dist","cli.mjs"),path.join(root,"scripts","init-deck.ts"),"--spec",path.join(td,"spec.json"),"--design",path.join(td,"design.md"),"--assets-root",td,"--output",out],{encoding:"utf8"});
  assert.equal(cp.status,0,cp.stdout+cp.stderr); const zip=await JSZip.loadAsync(await readFile(out)); const names=Object.keys(zip.files);
  assert(names.some(n=>n.startsWith("ppt/charts/chart"))); assert(names.some(n=>n.startsWith("ppt/media/"))); assert(names.some(n=>n.startsWith("ppt/notesSlides/notesSlide"))); assert(names.some(n=>n.startsWith("ppt/slideMasters/slideMaster")));
  const slides=(await Promise.all(names.filter(n=>/^ppt\/slides\/slide\d+\.xml$/.test(n)).map(n=>zip.file(n).async("string")))).join("\n"); assert.match(slides,/<a:tbl>/);
});
