// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class Wake_Time : ModuleRules
{
	public Wake_Time(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"AIModule",
			"StateTreeModule",
			"GameplayStateTreeModule",
			"UMG",
			"Slate"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { });

		PublicIncludePaths.AddRange(new string[] {
			"Wake_Time",
			"Wake_Time/Variant_Platforming",
			"Wake_Time/Variant_Platforming/Animation",
			"Wake_Time/Variant_Combat",
			"Wake_Time/Variant_Combat/AI",
			"Wake_Time/Variant_Combat/Animation",
			"Wake_Time/Variant_Combat/Gameplay",
			"Wake_Time/Variant_Combat/Interfaces",
			"Wake_Time/Variant_Combat/UI",
			"Wake_Time/Variant_SideScrolling",
			"Wake_Time/Variant_SideScrolling/AI",
			"Wake_Time/Variant_SideScrolling/Gameplay",
			"Wake_Time/Variant_SideScrolling/Interfaces",
			"Wake_Time/Variant_SideScrolling/UI"
		});

		// Uncomment if you are using Slate UI
		// PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore" });

		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
