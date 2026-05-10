#include "GreenBoxActor.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/Material.h"
#include "Engine/StaticMesh.h"

AGreenBoxActor::AGreenBoxActor()
{
    // Set this actor to call Tick() every frame
    PrimaryActorTick.bCanEverTick = true;
    
    // Create the static mesh component
    BoxMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BoxMesh"));
    RootComponent = BoxMesh;
    
    // Set a default static mesh (a cube)
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube"));
    if (CubeMesh.Succeeded())
    {
        BoxMesh->SetStaticMesh(CubeMesh.Object);
    }
    
    // Set a default green material
    static ConstructorHelpers::FObjectFinder<UMaterial> GreenMaterial(TEXT("/Engine/BasicShapes/BasicShapeMaterial"));
    if (GreenMaterial.Succeeded())
    {
        BoxMesh->SetMaterial(0, GreenMaterial.Object);
    }
    else
    {
        // Create a simple green material dynamically if the basic material isn't available
        // This is a fallback - in a real project you'd create a proper material asset
    }
}

void AGreenBoxActor::BeginPlay()
{
    Super::BeginPlay();
}

void AGreenBoxActor::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
}