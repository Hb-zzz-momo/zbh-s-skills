import test from "node:test";
import assert from "node:assert/strict";
import {mkdtemp,writeFile,readFile} from "node:fs/promises";
import {tmpdir} from "node:os";
import path from "node:path";
import {spawnSync} from "node:child_process";

const root=path.resolve(import.meta.dirname,"..");
test("bounds checker accepts zero-thickness lines but rejects zero-height content",async()=>{
  const td=await mkdtemp(path.join(tmpdir(),"bounds-")); const spec={slides:[{slide_id:"S01",claim:"x",content_blocks:[],text_budget:{title:5,body:5}}]}; const manifest={slide_size:{width:13.333,height:7.5},elements:[{slide_id:"S01",component:"footer-rule",x:.5,y:7,w:12,h:0},{slide_id:"S01",component:"content-panel",x:1,y:1,w:3,h:0}]};
  await writeFile(path.join(td,"spec.json"),JSON.stringify(spec)); await writeFile(path.join(td,"manifest.json"),JSON.stringify(manifest)); const out=path.join(td,"out.json");
  const cp=spawnSync(process.execPath,[path.join(root,"node_modules","tsx","dist","cli.mjs"),path.join(root,"scripts","check-bounds.ts"),"--spec",path.join(td,"spec.json"),"--manifest",path.join(td,"manifest.json"),"--output",out],{encoding:"utf8"}); assert.equal(cp.status,2); const result=JSON.parse(await readFile(out,"utf8")); assert.equal(result.issues.length,1); assert.equal(result.issues[0].component,"content-panel");
});
