#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "JoystickSR04ReceiverHost.generated.h"

class UJoystickSR04ReceiverComponent;

UCLASS(Blueprintable)
class MCPGAMEPROJECT_API AJoystickSR04ReceiverHost : public AActor
{
	GENERATED_BODY()

public:
	AJoystickSR04ReceiverHost();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "JoystickSR04")
	TObjectPtr<UJoystickSR04ReceiverComponent> Receiver;
};
