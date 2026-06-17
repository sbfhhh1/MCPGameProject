#pragma once

#include "CoreMinimal.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "BronzeExhibitTypes.generated.h"

UENUM(BlueprintType)
enum class EBronzeExhibitState : uint8
{
	Initializing,
	Browsing,
	AutoPlaying,
	Paused,
	Finished
};

USTRUCT(BlueprintType)
struct MCPGAMEPROJECT_API FBronzeExhibitPageRecord
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FName PageId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FText Kicker;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FText Title;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit", meta = (MultiLine = "true"))
	FText Body;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit", meta = (MultiLine = "true"))
	FText Detail;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FText Era;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FText Collection;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FText InteractionHint;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FLinearColor AccentColor = FLinearColor(0.62f, 0.35f, 0.13f, 1.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	TSoftObjectPtr<UTexture2D> HeroImage;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Artifact")
	TSoftObjectPtr<UStaticMesh> ArtifactMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Artifact")
	FTransform ArtifactTransform = FTransform::Identity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Artifact")
	bool bShowArtifact = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Artifact", meta = (ClampMin = "-180.0", ClampMax = "180.0"))
	float ArtifactRotationDegreesPerSecond = 12.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Playback", meta = (ClampMin = "1.0"))
	float AutoAdvanceSeconds = 12.0f;
};

USTRUCT(BlueprintType)
struct MCPGAMEPROJECT_API FBronzeExhibitChapterRecord
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FName ChapterId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FText Number;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FText Title;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FText Subtitle;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	TArray<FBronzeExhibitPageRecord> Pages;
};

