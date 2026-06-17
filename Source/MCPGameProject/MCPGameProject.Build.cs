// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class MCPGameProject : ModuleRules
{
	public MCPGameProject(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
	
		PublicDependencyModuleNames.AddRange(new string[] { 
			"Core", 
			"CoreUObject", 
			"Engine", 
			"InputCore", 
			"EnhancedInput",
			"UMG",  // Add UMG for Widget Blueprints
			"OpenClawBlenderGeometryNodes",
			"ProceduralMeshComponent",
			"AIModule",
			"NavigationSystem",
			"Niagara",
			"UDPWrapper"  // ESP32 WireEncoder UDP receiver
		});

		PrivateDependencyModuleNames.AddRange(new string[] {
			"Slate",
			"SlateCore",  // Required for UMG
			"Json",
			"Sockets",
			"Networking",
			"TobiiEyeTracker5",
			"UltraleapTracking"  // Leap Motion 手势：轮询掌心速度做左右挥手切模型
		});

		// 编辑器构建：用 Niagara 编辑器 API 程序化给粒子系统加力模块（MorphVortexEditorLibrary）。
		if (Target.bBuildEditor)
		{
			PrivateDependencyModuleNames.AddRange(new string[] {
				"UnrealEd",
				"NiagaraEditor"
			});
		}
	}
}
