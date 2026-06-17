#include "JoystickSR04ThirdPersonGameMode.h"

#include "JoystickSR04ThirdPersonCharacter.h"

AJoystickSR04ThirdPersonGameMode::AJoystickSR04ThirdPersonGameMode()
{
	DefaultPawnClass = AJoystickSR04ThirdPersonCharacter::StaticClass();
}
