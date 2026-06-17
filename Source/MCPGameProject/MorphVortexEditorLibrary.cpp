#include "MorphVortexEditorLibrary.h"

#include "NiagaraSystem.h"

#if WITH_EDITOR
#include "NiagaraEmitter.h"
#include "NiagaraScript.h"
#include "NiagaraScriptSource.h"
#include "NiagaraGraph.h"
#include "NiagaraNodeOutput.h"
#include "NiagaraNodeFunctionCall.h"
#include "ViewModels/Stack/NiagaraStackGraphUtilities.h"
#endif

int32 UMorphVortexEditorLibrary::AddModuleToParticleUpdate(UNiagaraSystem* System, const FString& ModuleAssetPath)
{
#if WITH_EDITOR
	if (!System)
	{
		UE_LOG(LogTemp, Warning, TEXT("[MorphVortex] System is null"));
		return 0;
	}

	UNiagaraScript* ModuleScript = LoadObject<UNiagaraScript>(nullptr, *ModuleAssetPath);
	if (!ModuleScript)
	{
		UE_LOG(LogTemp, Warning, TEXT("[MorphVortex] Failed to load module script: %s"), *ModuleAssetPath);
		return 0;
	}

	int32 AddedCount = 0;
	for (const FNiagaraEmitterHandle& Handle : System->GetEmitterHandles())
	{
		FVersionedNiagaraEmitter VersionedEmitter = Handle.GetInstance();
		FVersionedNiagaraEmitterData* EmitterData = VersionedEmitter.GetEmitterData();
		if (!EmitterData)
		{
			continue;
		}

		UNiagaraScriptSource* Source = Cast<UNiagaraScriptSource>(EmitterData->GraphSource);
		if (!Source || !Source->NodeGraph)
		{
			continue;
		}

		UNiagaraNodeOutput* OutputNode =
			Source->NodeGraph->FindEquivalentOutputNode(ENiagaraScriptUsage::ParticleUpdateScript);
		if (!OutputNode)
		{
			continue;
		}

		UNiagaraNodeFunctionCall* AddedModule =
			FNiagaraStackGraphUtilities::AddScriptModuleToStack(ModuleScript, *OutputNode);
		if (AddedModule)
		{
			++AddedCount;
			UE_LOG(LogTemp, Display, TEXT("[MorphVortex] Added module %s to emitter %s"),
				*ModuleScript->GetName(), *Handle.GetUniqueInstanceName());
		}
	}

	if (AddedCount > 0)
	{
		System->RequestCompile(false);
		System->MarkPackageDirty();
		UE_LOG(LogTemp, Display, TEXT("[MorphVortex] Added module to %d emitter(s); requested recompile."), AddedCount);
	}
	return AddedCount;
#else
	UE_LOG(LogTemp, Warning, TEXT("[MorphVortex] Editor-only function called in non-editor build"));
	return 0;
#endif
}
