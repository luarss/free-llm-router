#!/usr/bin/env node
/** Console entry point: `tollfree "prompt"` to chat, `tollfree probe` to check keys. */
import { chat } from "./index";
import { probeAll } from "./probe";

async function main(): Promise<void> {
  const argv = process.argv.slice(2);

  if (argv[0] === "probe") {
    await probeAll();
    return;
  }

  const q = argv.join(" ") || "Say hello in one short sentence.";
  const { text, meta } = (await chat({ prompt: q, returnMeta: true, verbose: true })) as {
    text: string;
    meta: { provider: string; model: string };
  };
  console.log(`\n--- ${meta.provider} / ${meta.model} ---`);
  console.log(text);
}

main().catch((e) => {
  console.error(e instanceof Error ? e.message : String(e));
  process.exit(1);
});
