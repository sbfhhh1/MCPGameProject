#include "BlenderGNRuntimePanelWidget.h"

#include "BlenderGNCageCornerMarkersComponent.h"
#include "BlenderGNIslandBreathMotionComponent.h"
#include "BlenderGNParasiteMotionComponent.h"
#include "BlenderGNWallNoiseMotionComponent.h"
#include "BlenderGeometryNodesComponent.h"
#include "BlenderGeometryNodesTypes.h"
#include "GameFramework/Actor.h"

void UBlenderGNRuntimePanelWidget::NativeConstruct()
{
	Super::NativeConstruct();
	if (!Target && GetOwningPlayerPawn())
	{
		ResolveReferences(GetOwningPlayerPawn());
	}
	ApplyRuntimeSettings();
	UpdateStatusText();
}

void UBlenderGNRuntimePanelWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	PumpQueuedRebuild();
	UpdateStatusText();
}

void UBlenderGNRuntimePanelWidget::ResolveReferences(AActor* SearchActor)
{
	if (!SearchActor)
	{
		return;
	}

	if (!Target)
	{
		Target = SearchActor->FindComponentByClass<UBlenderGeometryNodesComponent>();
	}
	if (!IslandMotion)
	{
		IslandMotion = SearchActor->FindComponentByClass<UBlenderGNIslandBreathMotionComponent>();
	}
	if (!ParasiteMotion)
	{
		ParasiteMotion = SearchActor->FindComponentByClass<UBlenderGNParasiteMotionComponent>();
	}
	if (!WallNoiseMotion)
	{
		WallNoiseMotion = SearchActor->FindComponentByClass<UBlenderGNWallNoiseMotionComponent>();
	}
	if (!CageCornerMarkers)
	{
		CageCornerMarkers = SearchActor->FindComponentByClass<UBlenderGNCageCornerMarkersComponent>();
	}
}

void UBlenderGNRuntimePanelWidget::ApplyRuntimeSettings()
{
	if (Target)
	{
		Target->RefreshMode = bDriveBlenderAnimation ? EBlenderGNRefreshMode::FixedInterval : EBlenderGNRefreshMode::Manual;
		Target->FixedRefreshInterval = 0.2f;
		Target->BlenderFrameRate = BlenderFrameRate;
	}
	SetLiveMotion(bLiveMotion);
}

void UBlenderGNRuntimePanelWidget::SetLiveMotion(bool bEnabled)
{
	bLiveMotion = bEnabled;
	if (IslandMotion)
	{
		IslandMotion->SetLiveMotion(bEnabled);
	}
	if (ParasiteMotion)
	{
		ParasiteMotion->SetLiveMotion(bEnabled);
	}
	if (WallNoiseMotion)
	{
		WallNoiseMotion->SetLiveMotion(bEnabled);
	}
}

void UBlenderGNRuntimePanelWidget::SetLiveBlenderRebuild(bool bEnabled)
{
	bLiveBlenderRebuild = bEnabled;
	if (!bLiveBlenderRebuild)
	{
		bRebuildQueued = false;
		bForceQueuedRebuild = false;
	}
}

void UBlenderGNRuntimePanelWidget::QueueBlenderRebuild(bool bForce, float DelayOverride)
{
	if (!Target || (!bForce && !bLiveBlenderRebuild))
	{
		return;
	}

	bRebuildQueued = true;
	bForceQueuedRebuild |= bForce;
	const float Delay = DelayOverride >= 0.0f ? DelayOverride : RebuildDebounceSeconds;
	const double Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
	RebuildAtSeconds = Target->bIsRunning ? Now : Now + Delay;
}

void UBlenderGNRuntimePanelWidget::RefreshNow()
{
	bRebuildQueued = false;
	bForceQueuedRebuild = false;
	if (Target)
	{
		Target->RefreshNow();
	}
}

void UBlenderGNRuntimePanelWidget::SetFloatInput(const FString& SocketName, float Value, bool bPreviewParasite)
{
	if (!Target)
	{
		return;
	}

	Target->SetFloatInput(SocketName, Value, false);
	if (bPreviewParasite && ParasiteMotion)
	{
		ParasiteMotion->SetGeometryPreview(SocketName, Value);
	}
	if (CageCornerMarkers && SocketName.Equals(TEXT("Corner Sphere Radius"), ESearchCase::IgnoreCase))
	{
		CageCornerMarkers->SetMarkerRadius(Value * Target->BlenderToUnrealScale);
	}
	QueueBlenderRebuild(true);
}

void UBlenderGNRuntimePanelWidget::SetIntInput(const FString& SocketName, int32 Value)
{
	if (Target)
	{
		Target->SetIntInput(SocketName, Value, false);
		QueueBlenderRebuild(true);
	}
}

void UBlenderGNRuntimePanelWidget::SetBoolInput(const FString& SocketName, bool bValue)
{
	if (Target)
	{
		Target->SetBoolInput(SocketName, bValue, false);
		QueueBlenderRebuild(true);
	}
}

void UBlenderGNRuntimePanelWidget::SetVectorInput(const FString& SocketName, FVector Value)
{
	if (Target)
	{
		Target->SetVectorInput(SocketName, Value, false);
		QueueBlenderRebuild(true);
	}
}

void UBlenderGNRuntimePanelWidget::SetWallNoiseStrength(float Value)
{
	if (WallNoiseMotion)
	{
		WallNoiseMotion->Strength = Value;
	}
	SetFloatInput(TEXT("Noise Strength"), Value, false);
}

void UBlenderGNRuntimePanelWidget::SetWallNoiseSpeed(float Value)
{
	if (WallNoiseMotion)
	{
		WallNoiseMotion->Speed = Value;
	}
	SetFloatInput(TEXT("Wave Speed"), Value, false);
}

void UBlenderGNRuntimePanelWidget::SetWallNoiseScale(float Value)
{
	if (WallNoiseMotion)
	{
		WallNoiseMotion->Scale = Value;
	}
	SetFloatInput(TEXT("Noise Scale"), Value, false);
}

void UBlenderGNRuntimePanelWidget::UpdateStatusText()
{
	RebuildStatusText = FString::Printf(TEXT("Blender Rebuild: %s"), bRebuildQueued ? TEXT("Queued") : (bLiveBlenderRebuild ? TEXT("Live") : TEXT("Manual")));
	if (!Target)
	{
		RuntimeStatusText = TEXT("No Geometry Nodes target");
		return;
	}

	RuntimeStatusText = FString::Printf(
		TEXT("%s\n%.2fs | %d verts | %d tris"),
		*Target->LastStatus,
		Target->LastEvaluationSeconds,
		Target->LastVertexCount,
		Target->LastTriangleCount);
}

void UBlenderGNRuntimePanelWidget::PumpQueuedRebuild()
{
	if (!bRebuildQueued || !Target)
	{
		return;
	}

	const double Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
	if (Now < RebuildAtSeconds || Target->bIsRunning)
	{
		return;
	}

	bRebuildQueued = false;
	const bool bForce = bForceQueuedRebuild;
	bForceQueuedRebuild = false;
	Target->RequestRefresh(bForce);
}
