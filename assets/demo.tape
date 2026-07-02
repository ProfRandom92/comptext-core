Output assets/demo.gif

# Terminal Settings
Set Shell "pwsh"
Set FontSize 16
Set FontFamily "Consolas"
Set Width 1200
Set Height 620
Set Padding 20
Set Theme "Dracula"
Set PlaybackSpeed 1.0

# Initialize demo environment (hidden commands)
Type "cd C:\CompText-SPARK-Sandbox-TESTING\CompText-SPARK-Sandbox\repos\comptext-forge" Enter
Sleep 500ms
Type "function comptext { comptext-cli $args }" Enter
Sleep 500ms
Type "Remove-Item -Path .comptext/keys/* -Force -ErrorAction SilentlyContinue" Enter
Sleep 500ms
Type "Clear-Host" Enter
Sleep 500ms

# Step 1: Type comptext and Enter — show the ANSI logo rendering (pause 2s to admire it)
Type "comptext"
Sleep 1s
Enter
Sleep 2s

# Exit the REPL to return to PowerShell shell
Type "/quit"
Sleep 500ms
Enter
Sleep 1s

# Step 2: Type comptext audit . --json and Enter — show a real audit run against comptext-forge itself (pause 2s)
Type "comptext audit . --json"
Sleep 1s
Enter
Sleep 2s

# Step 3: Type comptext keygen and Enter — show Ed25519 keypair generation (pause 1.5s)
Type "comptext keygen"
Sleep 1s
Enter
Sleep 1.5s

# Step 4: Type comptext capabilities --json | select -first 20 — show the capability contract (pause 1.5s)
Type "comptext capabilities --json | select -first 20"
Sleep 1s
Enter
Sleep 1.5s

# Step 5: Type comptext --help and Enter — show the full command list (pause 2s)
Type "comptext --help"
Sleep 1s
Enter
Sleep 2s

# End with a 1s pause before the recording stops
Sleep 1s
