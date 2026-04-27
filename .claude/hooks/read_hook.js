async function main() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }

  const toolArgs = JSON.parse(Buffer.concat(chunks).toString());

  // Block Read/Grep tools targeting .env
  const readPath =
    toolArgs.tool_input?.file_path || toolArgs.tool_input?.path || "";

  if (readPath.includes(".env")) {
    console.error("You cannot read the .env file");
    process.exit(2);
  }

  // Block Bash commands that reference .env
  const command = toolArgs.tool_input?.command || "";
  if (command.includes(".env")) {
    console.error("You cannot run commands that access the .env file");
    process.exit(2);
  }
}
main();
