import sys
p = sys.argv[1]
s = open(p).read()
old = "    aarch64 {\n      applicationIdSuffix '.aarch64'\n      resValue \"string\", \"app_name\", \"RetroArch (AArch64)\""
new = "    aarch64 {\n      applicationIdSuffix '.aarch64.mod'\n      resValue \"string\", \"app_name\", \"RetroArch Mod\""
assert s.count(old) == 1, "trecho nao encontrado exatamente uma vez"
open(p, "w").write(s.replace(old, new))
print("ok")
