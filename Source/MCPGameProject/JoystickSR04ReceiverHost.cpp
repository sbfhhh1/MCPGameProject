#include "JoystickSR04ReceiverHost.h"

#include "JoystickSR04ReceiverComponent.h"

AJoystickSR04ReceiverHost::AJoystickSR04ReceiverHost()
{
	PrimaryActorTick.bCanEverTick = false;

	Receiver = CreateDefaultSubobject<UJoystickSR04ReceiverComponent>(TEXT("JoystickSR04Receiver"));
	Receiver->bDriveMoveTarget = false;

	Tags.AddUnique(TEXT("JoystickSR04Receiver"));
}
