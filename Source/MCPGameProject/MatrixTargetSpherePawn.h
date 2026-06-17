#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "MatrixTargetSpherePawn.generated.h"

class UStaticMeshComponent;

UCLASS()
class MCPGAMEPROJECT_API AMatrixTargetSpherePawn : public APawn
{
	GENERATED_BODY()

public:
	AMatrixTargetSpherePawn();

	virtual void Tick(float DeltaTime) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> SphereMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Control")
	double MoveSpeed = 650.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Control")
	double InputSmoothing = 14.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Control")
	bool bClampToMovementBounds = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Control")
	FVector2D MovementBoundsMin = FVector2D(-545.0, -545.0);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Control")
	FVector2D MovementBoundsMax = FVector2D(545.0, 545.0);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Control")
	bool bNotifyMatrixFieldsOnMove = true;

	UFUNCTION(BlueprintCallable, Category = "Control")
	void SetMovementBounds(FVector2D BoundsMin, FVector2D BoundsMax);

protected:
	virtual void BeginPlay() override;

private:
	FVector2D ReadMovementInput() const;
	void NotifyMatrixFields(float DeltaTime) const;

	FVector2D CurrentVelocity = FVector2D::ZeroVector;
};
