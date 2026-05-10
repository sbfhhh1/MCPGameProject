#include "BlenderGeometryNodesComponent.h"

#include "Async/Async.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "Interfaces/IPluginManager.h"
#include "JsonObjectConverter.h"
#include "Materials/MaterialInterface.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "ProceduralMeshComponent.h"
#include "KismetProceduralMeshLibrary.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

UBlenderGeometryNodesComponent::UBlenderGeometryNodesComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
#if WITH_EDITOR
	bTickInEditor = true;
#endif
	EnsureDefaults();
}

void UBlenderGeometryNodesComponent::EnsureDefaults()
{
	if (BlenderExecutable.IsEmpty())
	{
		BlenderExecutable = FindDefaultBlenderPath();
	}
	if (SidecarScriptPath.IsEmpty())
	{
		SidecarScriptPath = GetDefaultSidecarPath();
	}
	if (Inputs.Num() == 0)
	{
		FBlenderGNInput Subdivisions;
		Subdivisions.DisplayName = TEXT("Hex Subdivisions");
		Subdivisions.SocketName = TEXT("Hex Subdivisions");
		Subdivisions.Type = EBlenderGNParameterType::Int;
		Subdivisions.IntValue = 3;
		Subdivisions.SliderMin = 1.0f;
		Subdivisions.SliderMax = 3.0f;
		Inputs.Add(Subdivisions);

		FBlenderGNInput TileGap;
		TileGap.DisplayName = TEXT("Tile Gap");
		TileGap.SocketName = TEXT("Tile Gap");
		TileGap.Type = EBlenderGNParameterType::Float;
		TileGap.FloatValue = 0.42f;
		TileGap.SliderMin = 0.0f;
		TileGap.SliderMax = 0.72f;
		Inputs.Add(TileGap);
	}
}

void UBlenderGeometryNodesComponent::BeginPlay()
{
	Super::BeginPlay();
	EnsureDefaults();
	if (bRefreshOnBeginPlay)
	{
		RefreshNow();
	}
}

void UBlenderGeometryNodesComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Super::EndPlay(EndPlayReason);
}

void UBlenderGeometryNodesComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	const double Now = FPlatformTime::Seconds();
	if (bHasPendingRefresh && !bIsRunning && Now >= QueuedRefreshTime)
	{
		bHasPendingRefresh = false;
		RequestRefresh(true);
	}

	if (RefreshMode == EBlenderGNRefreshMode::FixedInterval && Now >= NextFixedRefreshTime)
	{
		NextFixedRefreshTime = Now + FMath::Max(0.1f, FixedRefreshInterval);
		RequestRefresh(true);
	}
	else if (RefreshMode == EBlenderGNRefreshMode::OnParameterChange)
	{
		const FString Hash = BuildRequestHash();
		if (!Hash.Equals(LastRequestHash, ESearchCase::CaseSensitive))
		{
			RequestRefresh(false);
		}
	}
}

#if WITH_EDITOR
void UBlenderGeometryNodesComponent::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);
	EnsureDefaults();
	BlenderTimeoutSeconds = FMath::Clamp(BlenderTimeoutSeconds, 1, 120);
	MinimumRefreshInterval = FMath::Clamp(MinimumRefreshInterval, 0.02f, 2.0f);
	FixedRefreshInterval = FMath::Clamp(FixedRefreshInterval, 0.1f, 10.0f);
	BlenderFrameRate = FMath::Clamp(BlenderFrameRate, 1.0f, 60.0f);

	if (RefreshMode == EBlenderGNRefreshMode::OnParameterChange)
	{
		NotifyParametersChanged();
	}
}

#endif

void UBlenderGeometryNodesComponent::RefreshNow()
{
	RequestRefresh(true);
}

void UBlenderGeometryNodesComponent::RequestRefresh(bool bForce)
{
	EnsureDefaults();

	const FString Hash = BuildRequestHash();
	if (!bForce && Hash.Equals(LastRequestHash, ESearchCase::CaseSensitive))
	{
		return;
	}

	const double Now = FPlatformTime::Seconds();
	if (bIsRunning)
	{
		bHasPendingRefresh = true;
		QueuedRefreshTime = Now + FMath::Max(0.05f, MinimumRefreshInterval);
		LastStatus = TEXT("Refresh queued while Blender is still evaluating.");
		return;
	}

	if (!bForce)
	{
		const double Earliest = LastRefreshStartTime + MinimumRefreshInterval;
		if (Now < Earliest)
		{
			bHasPendingRefresh = true;
			QueuedRefreshTime = Earliest;
			LastStatus = TEXT("Refresh queued for rate limiting.");
			return;
		}
	}

	StartBackgroundRefresh(Hash);
}

void UBlenderGeometryNodesComponent::NotifyParametersChanged()
{
	RequestRefreshForParameterChange();
}

void UBlenderGeometryNodesComponent::RequestRefreshForParameterChange()
{
	if (RefreshMode == EBlenderGNRefreshMode::Manual)
	{
		RequestRefresh(true);
	}
	else if (RefreshMode == EBlenderGNRefreshMode::OnParameterChange)
	{
		RequestRefresh(false);
	}
}

void UBlenderGeometryNodesComponent::StartBackgroundRefresh(const FString& RequestHash)
{
	FString ScriptPath;
	const FString Error = ValidatePaths(ScriptPath);
	if (!Error.IsEmpty())
	{
		LastStatus = Error;
		bIsRunning = false;
		return;
	}

	bIsRunning = true;
	bHasPendingRefresh = false;
	ActiveRequestHash = RequestHash;
	LastRefreshStartTime = FPlatformTime::Seconds();
	LastStatus = TEXT("Starting Blender...");

	const FString WorkDir = FPaths::Combine(FPaths::ProjectIntermediateDir(), TEXT("OpenClawBlenderGeometryNodes"));
	IFileManager::Get().MakeDirectory(*WorkDir, true);
	const FString Guid = FGuid::NewGuid().ToString(EGuidFormats::Digits);
	const FString RequestPath = FPaths::Combine(WorkDir, FString::Printf(TEXT("gn_request_%s.json"), *Guid));
	const FString MeshPath = FPaths::Combine(WorkDir, FString::Printf(TEXT("gn_mesh_%s.%s"), *Guid, bUseBinaryMeshCache ? TEXT("bin") : TEXT("json")));
	FFileHelper::SaveStringToFile(BuildRequestJson(MeshPath), *RequestPath);

	const FString Arguments = BuildBlenderArguments(ScriptPath, RequestPath);
	const FString WorkingDirectory = FPaths::GetPath(BlendFile.FilePath);
	const FString BlenderExe = BlenderExecutable;
	const int32 TimeoutSeconds = BlenderTimeoutSeconds;
	const float Scale = BlenderToUnrealScale;
	const bool bShouldSmoothNormals = bSmoothNormalsByPosition;
	const float SmoothQuantization = NormalSmoothQuantization;
	TWeakObjectPtr<UBlenderGeometryNodesComponent> WeakThis(this);

	Async(EAsyncExecution::ThreadPool, [WeakThis, BlenderExe, Arguments, WorkingDirectory, MeshPath, TimeoutSeconds, Scale, bShouldSmoothNormals, SmoothQuantization]()
	{
		UBlenderGeometryNodesComponent::FEvalResult Result;
		const double Start = FPlatformTime::Seconds();
		FProcHandle Process = FPlatformProcess::CreateProc(*BlenderExe, *Arguments, true, true, true, nullptr, 0, *WorkingDirectory, nullptr);
		if (!Process.IsValid())
		{
			Result.Status = TEXT("Failed to start Blender.");
		}
		else
		{
			bool bTimedOut = false;
			while (FPlatformProcess::IsProcRunning(Process))
			{
				if (FPlatformTime::Seconds() - Start > TimeoutSeconds)
				{
					FPlatformProcess::TerminateProc(Process, true);
					bTimedOut = true;
					break;
				}
				FPlatformProcess::Sleep(0.015f);
			}

			int32 ReturnCode = 0;
			FPlatformProcess::GetProcReturnCode(Process, &ReturnCode);
			FPlatformProcess::CloseProc(Process);
			Result.ElapsedSeconds = static_cast<float>(FPlatformTime::Seconds() - Start);

			if (bTimedOut)
			{
				Result.Status = FString::Printf(TEXT("Blender timed out after %ds."), TimeoutSeconds);
			}
			else if (ReturnCode != 0 || !FPaths::FileExists(MeshPath))
			{
				Result.Status = FString::Printf(TEXT("Blender export failed. ExitCode=%d"), ReturnCode);
			}
			else
			{
				FString Error;
				bool bReadOk = false;
				if (MeshPath.EndsWith(TEXT(".bin")))
				{
					bReadOk = UBlenderGeometryNodesComponent::ReadBinaryMeshCache(MeshPath, Scale, Result.MeshData, Error);
				}
				else
				{
					FString JsonText;
					FFileHelper::LoadFileToString(JsonText, *MeshPath);
					bReadOk = UBlenderGeometryNodesComponent::ReadJsonMeshCache(JsonText, Scale, Result.MeshData, Error);
				}
				Result.bSuccess = bReadOk;
				if (Result.bSuccess && bShouldSmoothNormals)
				{
					UBlenderGeometryNodesComponent::SmoothNormalsByPosition(Result.MeshData, SmoothQuantization);
				}
				Result.Status = bReadOk ? TEXT("Blender Geometry Nodes mesh updated.") : Error;
			}
		}

		AsyncTask(ENamedThreads::GameThread, [WeakThis, Result]()
		{
			if (!WeakThis.IsValid())
			{
				return;
			}
			UBlenderGeometryNodesComponent* Component = WeakThis.Get();
			Component->bIsRunning = false;
			Component->LastEvaluationSeconds = Result.ElapsedSeconds;
			Component->LastStatus = Result.Status;
			if (Result.bSuccess)
			{
				Component->LastRequestHash = Component->ActiveRequestHash;
				Component->ApplyMeshData(Result.MeshData);
			}
		});
	});
}

FString UBlenderGeometryNodesComponent::ValidatePaths(FString& OutScriptPath) const
{
	OutScriptPath = SidecarScriptPath;
	if (OutScriptPath.IsEmpty())
	{
		OutScriptPath = GetDefaultSidecarPath();
	}
	if (BlenderExecutable.IsEmpty() || !FPaths::FileExists(BlenderExecutable))
	{
		return TEXT("Blender executable is missing or invalid.");
	}
	if (BlendFile.FilePath.IsEmpty() || !FPaths::FileExists(BlendFile.FilePath))
	{
		return TEXT("Blend file is missing or invalid.");
	}
	if (OutScriptPath.IsEmpty() || !FPaths::FileExists(OutScriptPath))
	{
		return TEXT("Blender sidecar script is missing or invalid.");
	}
	if (ObjectName.IsEmpty())
	{
		return TEXT("Object Name is empty.");
	}
	return FString();
}

FString UBlenderGeometryNodesComponent::BuildBlenderArguments(const FString& ScriptPath, const FString& RequestPath) const
{
	return FString::Printf(TEXT("-b \"%s\" --python \"%s\" -- \"%s\""), *BlendFile.FilePath, *ScriptPath, *RequestPath);
}

FString UBlenderGeometryNodesComponent::BuildRequestJson(const FString& MeshOutputPath) const
{
	TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("objectName"), ObjectName);
	Root->SetStringField(TEXT("modifierName"), ModifierName);
	Root->SetStringField(TEXT("outputPath"), MeshOutputPath);
	Root->SetStringField(TEXT("meshFormat"), bUseBinaryMeshCache ? TEXT("binary") : TEXT("json"));
	Root->SetNumberField(TEXT("frameRate"), BlenderFrameRate);
	const double WorldTime = GetWorld() ? GetWorld()->GetTimeSeconds() : FPlatformTime::Seconds();
	Root->SetNumberField(TEXT("unityTime"), WorldTime);
	Root->SetNumberField(TEXT("frame"), BlenderFrameOffset + FMath::RoundToInt(WorldTime * BlenderFrameRate));

	TArray<TSharedPtr<FJsonValue>> InputValues;
	for (const FBlenderGNInput& Input : Inputs)
	{
		TSharedRef<FJsonObject> Item = MakeShared<FJsonObject>();
		Item->SetStringField(TEXT("name"), Input.SocketName);
		Item->SetStringField(TEXT("fallbackIdentifier"), Input.FallbackIdentifier);
		switch (Input.Type)
		{
		case EBlenderGNParameterType::Int:
			Item->SetNumberField(TEXT("value"), Input.IntValue);
			break;
		case EBlenderGNParameterType::Bool:
			Item->SetBoolField(TEXT("value"), Input.BoolValue);
			break;
		case EBlenderGNParameterType::Vector3:
			{
				TArray<TSharedPtr<FJsonValue>> Vector;
				Vector.Add(MakeShared<FJsonValueNumber>(Input.VectorValue.X));
				Vector.Add(MakeShared<FJsonValueNumber>(Input.VectorValue.Y));
				Vector.Add(MakeShared<FJsonValueNumber>(Input.VectorValue.Z));
				Item->SetArrayField(TEXT("value"), Vector);
			}
			break;
		default:
			Item->SetNumberField(TEXT("value"), Input.FloatValue);
			break;
		}
		InputValues.Add(MakeShared<FJsonValueObject>(Item));
	}
	Root->SetArrayField(TEXT("inputs"), InputValues);

	FString Output;
	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Output);
	FJsonSerializer::Serialize(Root, Writer);
	return Output;
}

FString UBlenderGeometryNodesComponent::BuildRequestHash() const
{
	FString InputHash;
	for (const FBlenderGNInput& Input : Inputs)
	{
		InputHash += FString::Printf(
			TEXT("|%s|%s|%s|%d|%d|%.9g|%d|%.9g|%.9g|%.9g"),
			*Input.DisplayName,
			*Input.SocketName,
			*Input.FallbackIdentifier,
			static_cast<int32>(Input.Type),
			Input.IntValue,
			Input.FloatValue,
			Input.BoolValue ? 1 : 0,
			Input.VectorValue.X,
			Input.VectorValue.Y,
			Input.VectorValue.Z);
	}
	return FString::Printf(TEXT("%s|%s|%s|%s|%d%s"), *BlenderExecutable, *BlendFile.FilePath, *ObjectName, *ModifierName, bUseBinaryMeshCache ? 1 : 0, *InputHash);
}

void UBlenderGeometryNodesComponent::ApplyMeshData(const FBlenderGNMeshData& MeshData)
{
	LastMeshData = MeshData;
	LastVertexCount = LastMeshData.Vertices.Num();
	LastTriangleCount = LastMeshData.GetTriangleCount();

	UProceduralMeshComponent* ProceduralMesh = EnsureProceduralMesh();
	if (!ProceduralMesh)
	{
		LastStatus = TEXT("Could not create ProceduralMeshComponent.");
		return;
	}

	ProceduralMesh->ClearAllMeshSections();
	for (int32 SectionIndex = 0; SectionIndex < LastMeshData.Sections.Num(); ++SectionIndex)
	{
		const FBlenderGNMeshSection& Section = LastMeshData.Sections[SectionIndex];
		TArray<FLinearColor> VertexColors;
		TArray<FProcMeshTangent> Tangents;
		TArray<FVector> CalculatedNormals;
		UKismetProceduralMeshLibrary::CalculateTangentsForMesh(LastMeshData.Vertices, Section.Triangles, LastMeshData.UVs, CalculatedNormals, Tangents);
		ProceduralMesh->CreateMeshSection_LinearColor(
			SectionIndex,
			LastMeshData.Vertices,
			Section.Triangles,
			bApplyImportedNormals ? LastMeshData.Normals : CalculatedNormals,
			LastMeshData.UVs,
			VertexColors,
			Tangents,
			false);

		if (MaterialOverrides.IsValidIndex(SectionIndex) && MaterialOverrides[SectionIndex])
		{
			ProceduralMesh->SetMaterial(SectionIndex, MaterialOverrides[SectionIndex]);
		}
		else if (FallbackMaterial)
		{
			ProceduralMesh->SetMaterial(SectionIndex, FallbackMaterial);
		}
	}

	OnMeshUpdated.Broadcast(ProceduralMesh);
}

void UBlenderGeometryNodesComponent::ReapplyLastMeshData()
{
	if (LastMeshData.Vertices.Num() == 0 || LastMeshData.Triangles.Num() == 0)
	{
		return;
	}
	ApplyMeshData(LastMeshData);
}

UProceduralMeshComponent* UBlenderGeometryNodesComponent::EnsureProceduralMesh()
{
	if (CachedProceduralMesh)
	{
		return CachedProceduralMesh;
	}

	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return nullptr;
	}

	CachedProceduralMesh = Owner->FindComponentByClass<UProceduralMeshComponent>();
	if (!CachedProceduralMesh)
	{
		CachedProceduralMesh = NewObject<UProceduralMeshComponent>(Owner, TEXT("BlenderGN_ProceduralMesh"));
		CachedProceduralMesh->SetupAttachment(Owner->GetRootComponent());
		CachedProceduralMesh->RegisterComponent();
		Owner->AddInstanceComponent(CachedProceduralMesh);
	}
	if (!Owner->GetRootComponent())
	{
		Owner->SetRootComponent(CachedProceduralMesh);
	}
	return CachedProceduralMesh;
}

UProceduralMeshComponent* UBlenderGeometryNodesComponent::GetProceduralMesh() const
{
	if (CachedProceduralMesh)
	{
		return CachedProceduralMesh;
	}
	return GetOwner() ? GetOwner()->FindComponentByClass<UProceduralMeshComponent>() : nullptr;
}

FBlenderGNInput* UBlenderGeometryNodesComponent::FindInput(const FString& SocketName)
{
	for (FBlenderGNInput& Input : Inputs)
	{
		if (Input.MatchesName(SocketName))
		{
			return &Input;
		}
	}
	return nullptr;
}

const FBlenderGNInput* UBlenderGeometryNodesComponent::FindInput(const FString& SocketName) const
{
	for (const FBlenderGNInput& Input : Inputs)
	{
		if (Input.MatchesName(SocketName))
		{
			return &Input;
		}
	}
	return nullptr;
}

void UBlenderGeometryNodesComponent::SetFloatInput(const FString& SocketName, float Value, bool bRefresh)
{
	if (FBlenderGNInput* Input = FindInput(SocketName))
	{
		Input->Type = EBlenderGNParameterType::Float;
		Input->FloatValue = Value;
		if (bRefresh)
		{
			RequestRefreshForParameterChange();
		}
	}
}

void UBlenderGeometryNodesComponent::SetIntInput(const FString& SocketName, int32 Value, bool bRefresh)
{
	if (FBlenderGNInput* Input = FindInput(SocketName))
	{
		Input->Type = EBlenderGNParameterType::Int;
		Input->IntValue = Input->MatchesName(TEXT("Hex Subdivisions")) ? FMath::Clamp(Value, 1, 3) : Value;
		if (bRefresh)
		{
			RequestRefreshForParameterChange();
		}
	}
}

void UBlenderGeometryNodesComponent::SetBoolInput(const FString& SocketName, bool Value, bool bRefresh)
{
	if (FBlenderGNInput* Input = FindInput(SocketName))
	{
		Input->Type = EBlenderGNParameterType::Bool;
		Input->BoolValue = Value;
		if (bRefresh)
		{
			RequestRefreshForParameterChange();
		}
	}
}

void UBlenderGeometryNodesComponent::SetVectorInput(const FString& SocketName, FVector Value, bool bRefresh)
{
	if (FBlenderGNInput* Input = FindInput(SocketName))
	{
		Input->Type = EBlenderGNParameterType::Vector3;
		Input->VectorValue = Value;
		if (bRefresh)
		{
			RequestRefreshForParameterChange();
		}
	}
}

float UBlenderGeometryNodesComponent::GetFloatInput(const FString& SocketName, float Fallback) const
{
	const FBlenderGNInput* Input = FindInput(SocketName);
	return Input ? Input->FloatValue : Fallback;
}

int32 UBlenderGeometryNodesComponent::GetIntInput(const FString& SocketName, int32 Fallback) const
{
	const FBlenderGNInput* Input = FindInput(SocketName);
	return Input ? Input->IntValue : Fallback;
}

bool UBlenderGeometryNodesComponent::GetBoolInput(const FString& SocketName, bool Fallback) const
{
	const FBlenderGNInput* Input = FindInput(SocketName);
	return Input ? Input->BoolValue : Fallback;
}

FVector UBlenderGeometryNodesComponent::GetVectorInput(const FString& SocketName, FVector Fallback) const
{
	const FBlenderGNInput* Input = FindInput(SocketName);
	return Input ? Input->VectorValue : Fallback;
}

bool UBlenderGeometryNodesComponent::ReadJsonMeshCache(const FString& JsonText, float Scale, FBlenderGNMeshData& OutMeshData, FString& OutError)
{
	TSharedPtr<FJsonObject> Root;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
	if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
	{
		OutError = TEXT("Failed to parse Blender mesh cache JSON.");
		return false;
	}

	OutMeshData.Reset();
	OutMeshData.ObjectName = Root->GetStringField(TEXT("objectName"));

	const TArray<TSharedPtr<FJsonValue>>* Vertices = nullptr;
	const TArray<TSharedPtr<FJsonValue>>* Normals = nullptr;
	const TArray<TSharedPtr<FJsonValue>>* UVs = nullptr;
	const TArray<TSharedPtr<FJsonValue>>* Triangles = nullptr;
	const TArray<TSharedPtr<FJsonValue>>* MaterialIndices = nullptr;
	Root->TryGetArrayField(TEXT("vertices"), Vertices);
	Root->TryGetArrayField(TEXT("normals"), Normals);
	Root->TryGetArrayField(TEXT("uvs"), UVs);
	Root->TryGetArrayField(TEXT("triangles"), Triangles);
	Root->TryGetArrayField(TEXT("materialIndices"), MaterialIndices);

	if (!Vertices || !Triangles || Vertices->Num() % 3 != 0 || Triangles->Num() % 3 != 0)
	{
		OutError = TEXT("Blender mesh cache is missing vertices or triangles.");
		return false;
	}

	for (int32 Index = 0; Index + 2 < Vertices->Num(); Index += 3)
	{
		OutMeshData.Vertices.Add(ConvertPosition((*Vertices)[Index]->AsNumber(), (*Vertices)[Index + 1]->AsNumber(), (*Vertices)[Index + 2]->AsNumber(), Scale));
	}
	if (Normals && Normals->Num() == Vertices->Num())
	{
		for (int32 Index = 0; Index + 2 < Normals->Num(); Index += 3)
		{
			OutMeshData.Normals.Add(ConvertNormal((*Normals)[Index]->AsNumber(), (*Normals)[Index + 1]->AsNumber(), (*Normals)[Index + 2]->AsNumber()));
		}
	}
	if (UVs)
	{
		for (int32 Index = 0; Index + 1 < UVs->Num(); Index += 2)
		{
			OutMeshData.UVs.Add(FVector2D((*UVs)[Index]->AsNumber(), 1.0 - (*UVs)[Index + 1]->AsNumber()));
		}
	}
	while (OutMeshData.UVs.Num() < OutMeshData.Vertices.Num())
	{
		OutMeshData.UVs.Add(FVector2D::ZeroVector);
	}

	for (int32 Index = 0; Index + 2 < Triangles->Num(); Index += 3)
	{
		OutMeshData.Triangles.Add((*Triangles)[Index]->AsNumber());
		OutMeshData.Triangles.Add((*Triangles)[Index + 2]->AsNumber());
		OutMeshData.Triangles.Add((*Triangles)[Index + 1]->AsNumber());
	}
	if (MaterialIndices)
	{
		for (const TSharedPtr<FJsonValue>& Value : *MaterialIndices)
		{
			OutMeshData.MaterialIndices.Add(static_cast<int32>(Value->AsNumber()));
		}
	}

	const TArray<TSharedPtr<FJsonValue>>* Names = nullptr;
	const TArray<TSharedPtr<FJsonValue>>* Colors = nullptr;
	const TArray<TSharedPtr<FJsonValue>>* Metallic = nullptr;
	const TArray<TSharedPtr<FJsonValue>>* Roughness = nullptr;
	Root->TryGetArrayField(TEXT("materialNames"), Names);
	Root->TryGetArrayField(TEXT("materialBaseColors"), Colors);
	Root->TryGetArrayField(TEXT("materialMetallic"), Metallic);
	Root->TryGetArrayField(TEXT("materialRoughness"), Roughness);
	const int32 MaterialCount = Names ? Names->Num() : 0;
	for (int32 Index = 0; Index < MaterialCount; ++Index)
	{
		FBlenderGNMaterialInfo Info;
		Info.Name = (*Names)[Index]->AsString();
		const int32 ColorOffset = Index * 4;
		if (Colors && Colors->IsValidIndex(ColorOffset + 3))
		{
			Info.BaseColor = FLinearColor((*Colors)[ColorOffset]->AsNumber(), (*Colors)[ColorOffset + 1]->AsNumber(), (*Colors)[ColorOffset + 2]->AsNumber(), (*Colors)[ColorOffset + 3]->AsNumber());
		}
		if (Metallic && Metallic->IsValidIndex(Index))
		{
			Info.Metallic = (*Metallic)[Index]->AsNumber();
		}
		if (Roughness && Roughness->IsValidIndex(Index))
		{
			Info.Roughness = (*Roughness)[Index]->AsNumber();
		}
		OutMeshData.Materials.Add(Info);
	}

	if (OutMeshData.Normals.Num() != OutMeshData.Vertices.Num())
	{
		OutMeshData.Normals.Reset();
	}
	NormalizeTriangleWindingAndNormals(OutMeshData);
	OutMeshData.BuildSections();
	return true;
}

bool UBlenderGeometryNodesComponent::ReadBinaryMeshCache(const FString& FilePath, float Scale, FBlenderGNMeshData& OutMeshData, FString& OutError)
{
	TArray<uint8> Bytes;
	if (!FFileHelper::LoadFileToArray(Bytes, *FilePath) || Bytes.Num() < 16)
	{
		OutError = TEXT("Failed to read Blender binary mesh cache.");
		return false;
	}

	const uint8 Magic[] = { 'O', 'C', 'G', 'N', 'M', 'E', 'S', 'H' };
	int32 Offset = 0;
	auto Need = [&Bytes, &Offset](int32 Count) { return Count >= 0 && Offset + Count <= Bytes.Num(); };
	auto ReadU32 = [&Bytes, &Offset, &Need](uint32& OutValue) -> bool
	{
		if (!Need(4))
		{
			return false;
		}
		OutValue = static_cast<uint32>(Bytes[Offset]) |
			(static_cast<uint32>(Bytes[Offset + 1]) << 8) |
			(static_cast<uint32>(Bytes[Offset + 2]) << 16) |
			(static_cast<uint32>(Bytes[Offset + 3]) << 24);
		Offset += 4;
		return true;
	};
	auto ReadString = [&Bytes, &Offset, &Need, &ReadU32](FString& OutValue) -> bool
	{
		uint32 Length = 0;
		if (!ReadU32(Length) || !Need(static_cast<int32>(Length)))
		{
			return false;
		}
		FUTF8ToTCHAR Converted(reinterpret_cast<const ANSICHAR*>(Bytes.GetData() + Offset), Length);
		OutValue = FString(Converted.Length(), Converted.Get());
		Offset += Length;
		return true;
	};
	auto ReadFloatArray = [&Bytes, &Offset, &Need](TArray<float>& OutValues, int32 Count) -> bool
	{
		if (!Need(Count * 4))
		{
			return false;
		}
		OutValues.SetNum(Count);
		FMemory::Memcpy(OutValues.GetData(), Bytes.GetData() + Offset, Count * 4);
		Offset += Count * 4;
		return true;
	};
	auto ReadIntArray = [&Bytes, &Offset, &Need](TArray<int32>& OutValues, int32 Count) -> bool
	{
		if (!Need(Count * 4))
		{
			return false;
		}
		OutValues.SetNum(Count);
		FMemory::Memcpy(OutValues.GetData(), Bytes.GetData() + Offset, Count * 4);
		Offset += Count * 4;
		return true;
	};

	if (!Need(8) || FMemory::Memcmp(Bytes.GetData(), Magic, 8) != 0)
	{
		OutError = TEXT("Unsupported Blender GN binary cache magic.");
		return false;
	}
	Offset += 8;
	uint32 Version = 0;
	if (!ReadU32(Version) || (Version != 1 && Version != 2))
	{
		OutError = TEXT("Unsupported Blender GN binary cache version.");
		return false;
	}

	OutMeshData.Reset();
	if (!ReadString(OutMeshData.ObjectName))
	{
		OutError = TEXT("Malformed Blender GN binary object name.");
		return false;
	}

	uint32 VertexFloatCount = 0;
	uint32 NormalFloatCount = 0;
	uint32 UvFloatCount = 0;
	uint32 TriangleCount = 0;
	uint32 MaterialIndexCount = 0;
	if (!ReadU32(VertexFloatCount) || !ReadU32(NormalFloatCount) || !ReadU32(UvFloatCount) || !ReadU32(TriangleCount) || !ReadU32(MaterialIndexCount))
	{
		OutError = TEXT("Malformed Blender GN binary counts.");
		return false;
	}

	TArray<float> RawVertices;
	TArray<float> RawNormals;
	TArray<float> RawUvs;
	TArray<int32> RawTriangles;
	TArray<int32> RawMaterialIndices;
	if (!ReadFloatArray(RawVertices, VertexFloatCount) ||
		!ReadFloatArray(RawNormals, NormalFloatCount) ||
		!ReadFloatArray(RawUvs, UvFloatCount) ||
		!ReadIntArray(RawTriangles, TriangleCount) ||
		!ReadIntArray(RawMaterialIndices, MaterialIndexCount))
	{
		OutError = TEXT("Malformed Blender GN binary array data.");
		return false;
	}

	for (int32 Index = 0; Index + 2 < RawVertices.Num(); Index += 3)
	{
		OutMeshData.Vertices.Add(ConvertPosition(RawVertices[Index], RawVertices[Index + 1], RawVertices[Index + 2], Scale));
	}
	for (int32 Index = 0; Index + 2 < RawNormals.Num(); Index += 3)
	{
		OutMeshData.Normals.Add(ConvertNormal(RawNormals[Index], RawNormals[Index + 1], RawNormals[Index + 2]));
	}
	for (int32 Index = 0; Index + 1 < RawUvs.Num(); Index += 2)
	{
		OutMeshData.UVs.Add(FVector2D(RawUvs[Index], 1.0f - RawUvs[Index + 1]));
	}
	while (OutMeshData.UVs.Num() < OutMeshData.Vertices.Num())
	{
		OutMeshData.UVs.Add(FVector2D::ZeroVector);
	}
	for (int32 Index = 0; Index + 2 < RawTriangles.Num(); Index += 3)
	{
		OutMeshData.Triangles.Add(RawTriangles[Index]);
		OutMeshData.Triangles.Add(RawTriangles[Index + 2]);
		OutMeshData.Triangles.Add(RawTriangles[Index + 1]);
	}
	OutMeshData.MaterialIndices = MoveTemp(RawMaterialIndices);

	uint32 MaterialNameCount = 0;
	if (!ReadU32(MaterialNameCount))
	{
		OutError = TEXT("Malformed Blender GN binary material names.");
		return false;
	}
	for (uint32 Index = 0; Index < MaterialNameCount; ++Index)
	{
		FBlenderGNMaterialInfo Info;
		if (!ReadString(Info.Name))
		{
			OutError = TEXT("Malformed Blender GN binary material name.");
			return false;
		}
		OutMeshData.Materials.Add(Info);
	}
	if (OutMeshData.Normals.Num() != OutMeshData.Vertices.Num())
	{
		OutMeshData.Normals.Reset();
	}
	NormalizeTriangleWindingAndNormals(OutMeshData);
	OutMeshData.BuildSections();
	return true;
}

FVector UBlenderGeometryNodesComponent::ConvertPosition(float X, float Y, float Z, float Scale)
{
	return FVector(X * Scale, -Y * Scale, Z * Scale);
}

FVector UBlenderGeometryNodesComponent::ConvertNormal(float X, float Y, float Z)
{
	return FVector(X, -Y, Z).GetSafeNormal();
}

namespace
{
void FlipTriangleWinding(TArray<int32>& Triangles, int32 TriangleIndex)
{
	const int32 Offset = TriangleIndex * 3;
	Swap(Triangles[Offset + 1], Triangles[Offset + 2]);
}
}

void UBlenderGeometryNodesComponent::NormalizeTriangleWindingAndNormals(FBlenderGNMeshData& MeshData)
{
	const int32 TriangleCount = MeshData.Triangles.Num() / 3;
	if (MeshData.Vertices.Num() == 0 || TriangleCount == 0)
	{
		return;
	}

	const bool bHasImportedLoopNormals = MeshData.Normals.Num() == MeshData.Vertices.Num();
	if (bHasImportedLoopNormals)
	{
		for (int32 TriangleIndex = 0; TriangleIndex < TriangleCount; ++TriangleIndex)
		{
			const int32 Offset = TriangleIndex * 3;
			const int32 A = MeshData.Triangles[Offset];
			const int32 B = MeshData.Triangles[Offset + 1];
			const int32 C = MeshData.Triangles[Offset + 2];
			if (!MeshData.Vertices.IsValidIndex(A) || !MeshData.Vertices.IsValidIndex(B) || !MeshData.Vertices.IsValidIndex(C))
			{
				continue;
			}

			const FVector FaceNormal = FVector::CrossProduct(MeshData.Vertices[B] - MeshData.Vertices[A], MeshData.Vertices[C] - MeshData.Vertices[A]).GetSafeNormal();
			const FVector ImportedNormal = (MeshData.Normals[A] + MeshData.Normals[B] + MeshData.Normals[C]).GetSafeNormal();
			if (!FaceNormal.IsNearlyZero() && !ImportedNormal.IsNearlyZero() && FVector::DotProduct(FaceNormal, ImportedNormal) < 0.0f)
			{
				FlipTriangleWinding(MeshData.Triangles, TriangleIndex);
			}
		}

		for (FVector& Normal : MeshData.Normals)
		{
			Normal = Normal.IsNearlyZero() ? FVector::UpVector : Normal.GetSafeNormal();
		}
		return;
	}

	RecalculateNormalsForTriangleWinding(MeshData);
}

void UBlenderGeometryNodesComponent::RecalculateNormalsForTriangleWinding(FBlenderGNMeshData& MeshData)
{
	if (MeshData.Vertices.Num() == 0 || MeshData.Triangles.Num() == 0)
	{
		return;
	}

	MeshData.Normals.Reset();
	MeshData.Normals.SetNumZeroed(MeshData.Vertices.Num());

	for (int32 Index = 0; Index + 2 < MeshData.Triangles.Num(); Index += 3)
	{
		const int32 A = MeshData.Triangles[Index];
		const int32 B = MeshData.Triangles[Index + 1];
		const int32 C = MeshData.Triangles[Index + 2];
		if (!MeshData.Vertices.IsValidIndex(A) || !MeshData.Vertices.IsValidIndex(B) || !MeshData.Vertices.IsValidIndex(C))
		{
			continue;
		}

		const FVector FaceNormal = FVector::CrossProduct(MeshData.Vertices[B] - MeshData.Vertices[A], MeshData.Vertices[C] - MeshData.Vertices[A]).GetSafeNormal();
		if (FaceNormal.IsNearlyZero())
		{
			continue;
		}

		MeshData.Normals[A] += FaceNormal;
		MeshData.Normals[B] += FaceNormal;
		MeshData.Normals[C] += FaceNormal;
	}

	for (FVector& Normal : MeshData.Normals)
	{
		Normal = Normal.IsNearlyZero() ? FVector::UpVector : Normal.GetSafeNormal();
	}
}

void UBlenderGeometryNodesComponent::SmoothNormalsByPosition(FBlenderGNMeshData& MeshData, float Quantization)
{
	if (MeshData.Vertices.Num() == 0 || MeshData.Normals.Num() != MeshData.Vertices.Num())
	{
		return;
	}

	TMap<FIntVector, FVector> Sums;
	const float SafeQuantization = FMath::Max(1.0f, Quantization);
	for (int32 Index = 0; Index < MeshData.Vertices.Num(); ++Index)
	{
		const FVector& V = MeshData.Vertices[Index];
		const FIntVector Key(
			FMath::RoundToInt(V.X * SafeQuantization),
			FMath::RoundToInt(V.Y * SafeQuantization),
			FMath::RoundToInt(V.Z * SafeQuantization));
		Sums.FindOrAdd(Key) += MeshData.Normals[Index];
	}

	for (int32 Index = 0; Index < MeshData.Normals.Num(); ++Index)
	{
		const FVector& V = MeshData.Vertices[Index];
		const FIntVector Key(
			FMath::RoundToInt(V.X * SafeQuantization),
			FMath::RoundToInt(V.Y * SafeQuantization),
			FMath::RoundToInt(V.Z * SafeQuantization));
		if (const FVector* Sum = Sums.Find(Key))
		{
			MeshData.Normals[Index] = Sum->IsNearlyZero() ? MeshData.Normals[Index] : Sum->GetSafeNormal();
		}
	}
}

FString UBlenderGeometryNodesComponent::FindDefaultBlenderPath()
{
	const TCHAR* Candidates[] =
	{
		TEXT("C:/Program Files/Blender Foundation/Blender 5.1/blender.exe"),
		TEXT("C:/Program Files/Blender Foundation/Blender 5.0/blender.exe"),
		TEXT("C:/Program Files/Blender Foundation/Blender 4.4/blender.exe"),
		TEXT("C:/Program Files/Blender Foundation/Blender 4.3/blender.exe")
	};
	for (const TCHAR* Candidate : Candidates)
	{
		if (FPaths::FileExists(Candidate))
		{
			return Candidate;
		}
	}
	return FString();
}

FString UBlenderGeometryNodesComponent::GetDefaultSidecarPath()
{
	TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("OpenClawBlenderGeometryNodes"));
	return Plugin.IsValid() ? FPaths::Combine(Plugin->GetBaseDir(), TEXT("Content/Python/unreal_gn_eval.py")) : FString();
}
