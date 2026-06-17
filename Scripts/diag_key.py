"""
快速确认 unreal.Key 正确构造方式
exec(open(r"C:/UE_Project/MCPGameProject/Scripts/diag_key.py").read())
"""
import unreal

# 方式1: set_editor_property
try:
    k = unreal.Key()
    k.set_editor_property("key_name", "One")
    print(f"方式1 set_editor_property: {k}, key_name={k.get_editor_property('key_name')}")
except Exception as e:
    print(f"方式1 ❌: {e}")

# 方式2: 直接访问已知枚举成员
for attr in ["One","Two","Three","EKeys_One"]:
    k = getattr(unreal.Key, attr, None)
    if k is not None:
        print(f"方式2 unreal.Key.{attr}: {k}")

# 方式3: dir(unreal.Key) 找到所有静态成员
members = [m for m in dir(unreal.Key) if not m.startswith("_")]
print(f"\nunreal.Key 全部成员({len(members)}): {members[:30]}")

# 方式4: 实际调用 was_input_key_just_pressed 看它期望什么类型
print("\n── was_input_key_just_pressed 签名 ──")
try:
    print(unreal.PlayerController.was_input_key_just_pressed.__doc__)
except:
    pass
