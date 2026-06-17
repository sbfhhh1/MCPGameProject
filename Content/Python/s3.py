import unreal, json, os

r = {}

# 查找YZL Actor
actors = unreal.EditorLevelLibrary.get_all_level_actors()
yzl_names = []
for a in actors:
    n = a.get_name()
    if "part_00000001" in n or n == "YZL":
        yzl_names.append(n)

r["yzl_candidates"] = yzl_names

# 尝试查找所有actor名字
all_names = [a.get_name() for a in actors]
r["all_names"] = all_names

with open(os.path.join(os.environ["USERPROFILE"], "r3.json"), "w") as f:
    json.dump(r, f, indent=2)
