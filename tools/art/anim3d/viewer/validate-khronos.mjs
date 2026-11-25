#!/usr/bin/env node
import {readFile,writeFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const validator=require(process.env.GLTF_VALIDATOR_MODULE||'gltf-validator');
const input=process.argv[2];if(!input)throw new Error('Usage: validate-khronos.mjs asset.glb [report.json]');
const bytes=await readFile(input);
const report=await validator.validateBytes(new Uint8Array(bytes),{maxIssues:100});
if(process.argv[3])await writeFile(process.argv[3],JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report.issues,null,2));
if(report.issues.numErrors||report.issues.numWarnings)process.exitCode=1;
