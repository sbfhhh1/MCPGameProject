#include "BronzeArtifactStage.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"

ABronzeArtifactStage::ABronzeArtifactStage()
{
	PrimaryActorTick.bCanEverTick = true;

	StageRoot = CreateDefaultSubobject<USceneComponent>(TEXT("StageRoot"));
	SetRootComponent(StageRoot);

	ArtifactMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ArtifactMesh"));
	ArtifactMesh->SetupAttachment(StageRoot);
	ArtifactMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	ArtifactMesh->SetGenerateOverlapEvents(false);
	ArtifactMesh->SetCastShadow(true);
}

void ABronzeArtifactStage::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (bRotationEnabled && ArtifactMesh && ArtifactMesh->IsVisible() && !FMath::IsNearlyZero(CurrentRotationDegreesPerSecond))
	{
		ArtifactMesh->AddLocalRotation(FRotator(0.0f, CurrentRotationDegreesPerSecond * DeltaSeconds, 0.0f));
	}
}

void ABronzeArtifactStage::ApplyPage(const FBronzeExhibitPageRecord& Page)
{
	CurrentPageId = Page.PageId;
	CurrentRotationDegreesPerSecond = Page.ArtifactRotationDegreesPerSecond;

	if (!ArtifactMesh)
	{
		return;
	}

	UStaticMesh* Mesh = Page.ArtifactMesh.IsNull() ? nullptr : Page.ArtifactMesh.LoadSynchronous();
	ArtifactMesh->SetStaticMesh(Mesh);
	ArtifactMesh->SetRelativeTransform(Page.ArtifactTransform);
	ArtifactMesh->SetVisibility(Page.bShowArtifact && Mesh != nullptr, true);
}

void ABronzeArtifactStage::ClearArtifact()
{
	CurrentPageId = NAME_None;
	CurrentRotationDegreesPerSecond = 0.0f;
	if (ArtifactMesh)
	{
		ArtifactMesh->SetStaticMesh(nullptr);
		ArtifactMesh->SetVisibility(false, true);
	}
}

void ABronzeArtifactStage::SetArtifactRotationEnabled(bool bEnabled)
{
	bRotationEnabled = bEnabled;
}

