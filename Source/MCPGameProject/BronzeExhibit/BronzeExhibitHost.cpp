#include "BronzeExhibitHost.h"

#include "BronzeArtifactStage.h"
#include "BronzeExhibitWidget.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "UObject/UnrealType.h"

namespace
{
FText ExhibitText(const TCHAR* Text)
{
	return FText::FromString(Text);
}

FBronzeExhibitPageRecord MakePage(
	const TCHAR* PageId,
	const TCHAR* Kicker,
	const TCHAR* Title,
	const TCHAR* Body,
	const TCHAR* Detail,
	const TCHAR* Era,
	const TCHAR* Collection,
	const TCHAR* Hint,
	const FLinearColor& Accent,
	const TCHAR* ArtifactMeshPath,
	const FTransform& ArtifactTransform,
	float RotationDegreesPerSecond = 12.0f)
{
	FBronzeExhibitPageRecord Page;
	Page.PageId = FName(PageId);
	Page.Kicker = ExhibitText(Kicker);
	Page.Title = ExhibitText(Title);
	Page.Body = ExhibitText(Body);
	Page.Detail = ExhibitText(Detail);
	Page.Era = ExhibitText(Era);
	Page.Collection = ExhibitText(Collection);
	Page.InteractionHint = ExhibitText(Hint);
	Page.AccentColor = Accent;
	Page.ArtifactMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(ArtifactMeshPath));
	Page.ArtifactTransform = ArtifactTransform;
	Page.ArtifactRotationDegreesPerSecond = RotationDegreesPerSecond;
	return Page;
}

FBronzeExhibitChapterRecord MakeChapter(
	const TCHAR* ChapterId,
	const TCHAR* Number,
	const TCHAR* Title,
	const TCHAR* Subtitle,
	std::initializer_list<FBronzeExhibitPageRecord> Pages)
{
	FBronzeExhibitChapterRecord Chapter;
	Chapter.ChapterId = FName(ChapterId);
	Chapter.Number = ExhibitText(Number);
	Chapter.Title = ExhibitText(Title);
	Chapter.Subtitle = ExhibitText(Subtitle);
	for (const FBronzeExhibitPageRecord& Page : Pages)
	{
		Chapter.Pages.Add(Page);
	}
	return Chapter;
}

FTransform ArtifactTransform(const FVector& Location, const FRotator& Rotation, const FVector& Scale)
{
	return FTransform(Rotation, Location, Scale);
}
}

ABronzeExhibitHost::ABronzeExhibitHost()
{
	PrimaryActorTick.bCanEverTick = true;
	WidgetClass = UBronzeExhibitWidget::StaticClass();
	BuildDefaultChapters();
}

void ABronzeExhibitHost::BeginPlay()
{
	Super::BeginPlay();

	if (Chapters.IsEmpty())
	{
		BuildDefaultChapters();
	}

	ResolveOrSpawnStage();
	CreateRuntimeWidget();
	SetTobiiSimulationEnabled(bEnableTobiiSimulationAtStart);
	ApplyCurrentPage(false);
	SetState(bAutoPlayAtStart ? EBronzeExhibitState::AutoPlaying : EBronzeExhibitState::Browsing);
	RefreshWidget();
	UE_LOG(LogTemp, Display, TEXT("BronzeExhibit: runtime ready with %d chapters and %d pages."), Chapters.Num(), GetTotalPageCount());
}

void ABronzeExhibitHost::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (APlayerController* PlayerController = UGameplayStatics::GetPlayerController(this, 0))
	{
		if (PlayerController->WasInputKeyJustPressed(EKeys::F8))
		{
			ToggleTobiiSimulation();
		}
	}

	if (State != EBronzeExhibitState::AutoPlaying)
	{
		UpdateWidgetGaze();
		return;
	}

	CurrentPageElapsedSeconds += DeltaSeconds;
	if (CurrentPageElapsedSeconds >= GetCurrentPageDuration())
	{
		AdvancePage(true, false);
	}
	UpdateWidgetGaze();
}

void ABronzeExhibitHost::NextPage()
{
	AdvancePage(true, true);
}

void ABronzeExhibitHost::PreviousPage()
{
	AdvancePage(false, true);
}

bool ABronzeExhibitHost::SelectChapter(int32 ChapterIndex)
{
	return SelectPage(ChapterIndex, 0);
}

bool ABronzeExhibitHost::SelectPage(int32 ChapterIndex, int32 PageIndex)
{
	if (!Chapters.IsValidIndex(ChapterIndex) || !Chapters[ChapterIndex].Pages.IsValidIndex(PageIndex))
	{
		return false;
	}

	if (bPauseAutoPlayOnManualNavigation && State == EBronzeExhibitState::AutoPlaying)
	{
		SetState(EBronzeExhibitState::Paused);
	}
	else if (State == EBronzeExhibitState::Finished)
	{
		SetState(EBronzeExhibitState::Browsing);
	}

	CurrentChapterIndex = ChapterIndex;
	CurrentPageIndex = PageIndex;
	ApplyCurrentPage(true);
	return true;
}

bool ABronzeExhibitHost::SelectGlobalPage(int32 GlobalPageIndex)
{
	if (GlobalPageIndex < 0)
	{
		return false;
	}

	int32 RemainingPageIndex = GlobalPageIndex;
	for (int32 ChapterIndex = 0; ChapterIndex < Chapters.Num(); ++ChapterIndex)
	{
		if (RemainingPageIndex < Chapters[ChapterIndex].Pages.Num())
		{
			return SelectPage(ChapterIndex, RemainingPageIndex);
		}
		RemainingPageIndex -= Chapters[ChapterIndex].Pages.Num();
	}
	return false;
}

void ABronzeExhibitHost::StartAutoPlay()
{
	if (State == EBronzeExhibitState::Finished)
	{
		CurrentChapterIndex = 0;
		CurrentPageIndex = 0;
		ApplyCurrentPage(true);
	}

	if (GetTotalPageCount() > 0)
	{
		SetState(EBronzeExhibitState::AutoPlaying);
	}
}

void ABronzeExhibitHost::PauseAutoPlay()
{
	if (State == EBronzeExhibitState::AutoPlaying)
	{
		SetState(EBronzeExhibitState::Paused);
	}
}

void ABronzeExhibitHost::ToggleAutoPlay()
{
	if (State == EBronzeExhibitState::AutoPlaying)
	{
		PauseAutoPlay();
	}
	else
	{
		StartAutoPlay();
	}
}

void ABronzeExhibitHost::ToggleTobiiSimulation()
{
	SetTobiiSimulationEnabled(!IsTobiiSimulationEnabled());
}

bool ABronzeExhibitHost::SetTobiiSimulationEnabled(bool bEnabled)
{
	UObject* TobiiSubsystem = ResolveTobiiSubsystem();
	bool bReturnValue = false;
	if (!CallBoolFunction(TobiiSubsystem, TEXT("SetSimulationEnabled"), bEnabled, bReturnValue))
	{
		return false;
	}

	bLastTobiiSimulationState = bEnabled;
	OnTobiiSimulationChanged.Broadcast(bEnabled);
	CallWidgetFunction(TEXT("HandleTobiiSimulationChanged"));
	UE_LOG(LogTemp, Display, TEXT("BronzeExhibit: Tobii simulation %s."), bEnabled ? TEXT("enabled") : TEXT("disabled"));
	return true;
}

bool ABronzeExhibitHost::IsTobiiSimulationEnabled() const
{
	bool bEnabled = false;
	return CallBoolGetter(ResolveTobiiSubsystem(), TEXT("IsSimulationEnabled"), bEnabled) ? bEnabled : false;
}

void ABronzeExhibitHost::RefreshWidget()
{
	if (RuntimeWidget)
	{
		RuntimeWidget->SetPage(GetCurrentGlobalPageIndex(), false);
	}
	CallWidgetFunction(TEXT("HandleExhibitPageChanged"));
	CallWidgetFunction(TEXT("HandleExhibitStateChanged"));
	CallWidgetFunction(TEXT("HandleTobiiSimulationChanged"));
}

bool ABronzeExhibitHost::GetCurrentChapter(FBronzeExhibitChapterRecord& OutChapter) const
{
	if (!Chapters.IsValidIndex(CurrentChapterIndex))
	{
		return false;
	}

	OutChapter = Chapters[CurrentChapterIndex];
	return true;
}

bool ABronzeExhibitHost::GetCurrentPage(FBronzeExhibitPageRecord& OutPage) const
{
	if (!Chapters.IsValidIndex(CurrentChapterIndex) || !Chapters[CurrentChapterIndex].Pages.IsValidIndex(CurrentPageIndex))
	{
		return false;
	}

	OutPage = Chapters[CurrentChapterIndex].Pages[CurrentPageIndex];
	return true;
}

int32 ABronzeExhibitHost::GetTotalPageCount() const
{
	int32 Count = 0;
	for (const FBronzeExhibitChapterRecord& Chapter : Chapters)
	{
		Count += Chapter.Pages.Num();
	}
	return Count;
}

int32 ABronzeExhibitHost::GetCurrentGlobalPageIndex() const
{
	if (!Chapters.IsValidIndex(CurrentChapterIndex))
	{
		return INDEX_NONE;
	}

	int32 GlobalIndex = CurrentPageIndex;
	for (int32 ChapterIndex = 0; ChapterIndex < CurrentChapterIndex; ++ChapterIndex)
	{
		GlobalIndex += Chapters[ChapterIndex].Pages.Num();
	}
	return GlobalIndex;
}

float ABronzeExhibitHost::GetPageProgress() const
{
	return FMath::Clamp(CurrentPageElapsedSeconds / GetCurrentPageDuration(), 0.0f, 1.0f);
}

void ABronzeExhibitHost::BuildDefaultChapters()
{
	Chapters.Reset();

	const FLinearColor Bronze(0.62f, 0.34f, 0.12f, 1.0f);
	const FLinearColor Jade(0.19f, 0.48f, 0.39f, 1.0f);
	const FLinearColor Gold(0.82f, 0.58f, 0.18f, 1.0f);
	const FLinearColor Vermilion(0.66f, 0.16f, 0.10f, 1.0f);
	const FLinearColor Ink(0.20f, 0.24f, 0.25f, 1.0f);
	const TCHAR* Cube = TEXT("/Engine/BasicShapes/Cube.Cube");
	const TCHAR* Sphere = TEXT("/Engine/BasicShapes/Sphere.Sphere");
	const TCHAR* Cylinder = TEXT("/Engine/BasicShapes/Cylinder.Cylinder");
	const TCHAR* Cone = TEXT("/Engine/BasicShapes/Cone.Cone");

	Chapters.Add(MakeChapter(TEXT("origin"), TEXT("序章"), TEXT("起源"), TEXT("矿石、合金与范铸技术开启青铜时代。"), {
		MakePage(TEXT("origin_ore"), TEXT("材料起点"), TEXT("铜矿石与合金"),
			TEXT("天然铜和铜矿石是青铜文明的物质起点。锡与铅的加入，让铜液更适合复杂浇铸。"),
			TEXT("从矿料识别到合金配比，早期工匠建立了可重复的材料经验。"),
			TEXT("史前至早期青铜时代"), TEXT("材料技术"), TEXT("从矿石开始浏览完整时代流程"), Bronze,
			Sphere, ArtifactTransform(FVector(0, 0, 18), FRotator(0, 18, 0), FVector(1.25f, 0.85f, 0.72f)), 8.0f),
		MakePage(TEXT("origin_mold"), TEXT("制作起点"), TEXT("陶范与浇铸"),
			TEXT("模、外范与内范共同围成器物形状，铜液在其中冷却成为青铜器。"),
			TEXT("陶范铸造为之后大型礼器与精密纹饰奠定了技术基础。"),
			TEXT("早期青铜时代"), TEXT("铸造流程"), TEXT("观察占位陶范的分块轮廓"), Jade,
			Cube, ArtifactTransform(FVector(0, 0, 35), FRotator(8, 45, 0), FVector(1.05f, 0.82f, 1.45f)), 6.0f)
	}));

	Chapters.Add(MakeChapter(TEXT("xia"), TEXT("第一章"), TEXT("夏"), TEXT("二里头文化呈现早期王朝礼器体系。"), {
		MakePage(TEXT("xia_jue"), TEXT("二里头礼器"), TEXT("乳钉纹铜爵"),
			TEXT("铜爵是夏代晚期最具代表性的青铜礼器之一，器形轻巧而结构复杂。"),
			TEXT("爵的流、尾、柱与三足显示早期礼仪饮酒器已经形成稳定范式。"),
			TEXT("夏代晚期"), TEXT("二里头文化"), TEXT("旋转观察爵形比例"), Gold,
			Cone, ArtifactTransform(FVector(0, 0, 52), FRotator(0, -18, 0), FVector(0.78f, 0.78f, 1.55f)), 13.0f),
		MakePage(TEXT("xia_turquoise"), TEXT("权力标识"), TEXT("绿松石龙形器与兽面牌"),
			TEXT("绿松石片与铜质构件共同构成醒目的仪式物件，体现跨材料制作能力。"),
			TEXT("其发现位置与制作成本提示它们可能属于高等级身份与仪式活动。"),
			TEXT("夏代晚期"), TEXT("二里头宫殿区与墓葬"), TEXT("观察扁平化占位器的视觉中心"), Jade,
			Cube, ArtifactTransform(FVector(0, 0, 42), FRotator(10, 0, 12), FVector(1.7f, 0.28f, 0.82f)), 5.0f)
	}));

	Chapters.Add(MakeChapter(TEXT("shang"), TEXT("第二章"), TEXT("商"), TEXT("大型礼器、兽面纹与酒礼达到高峰。"), {
		MakePage(TEXT("shang_houmuwu"), TEXT("王权重器"), TEXT("后母戊鼎"),
			TEXT("后母戊鼎以巨大体量展示晚商铸造组织能力，是大型方鼎的代表。"),
			TEXT("器物从制范、熔铜到协同浇铸，需要严密的资源调度与专业分工。"),
			TEXT("商代晚期"), TEXT("大型礼器"), TEXT("感受方鼎占位器的体量与稳定性"), Bronze,
			Cube, ArtifactTransform(FVector(0, 0, 72), FRotator(0, 20, 0), FVector(1.55f, 1.15f, 1.45f)), 7.0f),
		MakePage(TEXT("shang_siyang"), TEXT("立体装饰"), TEXT("四羊方尊"),
			TEXT("四羊方尊将圆雕动物与方尊结构融为一体，展现分铸、铸接与装饰设计。"),
			TEXT("器身四角的羊首强化了礼器面向四方的视觉秩序。"),
			TEXT("商代晚期"), TEXT("酒礼与纹饰"), TEXT("观察四方展开的占位轮廓"), Gold,
			Cylinder, ArtifactTransform(FVector(0, 0, 62), FRotator(0, 45, 0), FVector(1.45f, 1.45f, 1.65f)), 11.0f),
		MakePage(TEXT("shang_fuhao_owl"), TEXT("女性与王室"), TEXT("妇好鸮尊"),
			TEXT("妇好墓出土的鸮尊兼具鸟形塑造与酒器功能，反映王室女性的身份与活动。"),
			TEXT("动物造型让礼器拥有鲜明的正面凝视与空间存在感。"),
			TEXT("商代晚期"), TEXT("妇好墓"), TEXT("注视鸟形占位器并切换下一时代"), Vermilion,
			Cone, ArtifactTransform(FVector(0, 0, 62), FRotator(-8, -25, 0), FVector(1.2f, 0.92f, 1.75f)), 15.0f)
	}));

	Chapters.Add(MakeChapter(TEXT("western_zhou"), TEXT("第三章"), TEXT("西周"), TEXT("铭文与列鼎制度重塑礼制秩序。"), {
		MakePage(TEXT("zhou_he_zun"), TEXT("中国铭文"), TEXT("何尊"),
			TEXT("何尊铭文包含早期“中国”一词，记录营建成周与王室政治记忆。"),
			TEXT("器物既是礼器，也是将重要事件铸入金属的历史档案。"),
			TEXT("西周早期"), TEXT("青铜铭文"), TEXT("将圆筒占位器视作铭文载体"), Gold,
			Cylinder, ArtifactTransform(FVector(0, 0, 58), FRotator(0, -35, 0), FVector(1.18f, 1.18f, 1.65f)), 9.0f),
		MakePage(TEXT("zhou_maogong_ding"), TEXT("长篇金文"), TEXT("毛公鼎"),
			TEXT("毛公鼎以长篇铭文记录周王册命，是西周晚期政治文书的重要见证。"),
			TEXT("铭文内容、器形与礼制共同构成可被代代传承的家族记忆。"),
			TEXT("西周晚期"), TEXT("册命与礼制"), TEXT("观察鼎形占位器的沉稳比例"), Bronze,
			Sphere, ArtifactTransform(FVector(0, 0, 54), FRotator(0, 12, 0), FVector(1.42f, 1.42f, 1.12f)), 10.0f)
	}));

	Chapters.Add(MakeChapter(TEXT("spring_autumn"), TEXT("第四章"), TEXT("春秋"), TEXT("诸侯竞争推动区域风格与铸造创新。"), {
		MakePage(TEXT("spring_lotus_crane"), TEXT("楚式想象"), TEXT("莲鹤方壶"),
			TEXT("莲鹤方壶以展翼仙鹤和层叠莲瓣突破传统礼器的庄严轮廓。"),
			TEXT("复杂附饰体现春秋时期区域审美与失蜡、分铸等技术探索。"),
			TEXT("春秋中期"), TEXT("新郑郑公大墓"), TEXT("观察高挑占位器的向上动势"), Jade,
			Cylinder, ArtifactTransform(FVector(0, 0, 78), FRotator(0, 28, 0), FVector(0.92f, 0.92f, 2.15f)), 12.0f),
		MakePage(TEXT("spring_wangziwu"), TEXT("楚国重器"), TEXT("王子午鼎"),
			TEXT("王子午鼎器身与附饰共同呈现楚国青铜艺术的繁复风格。"),
			TEXT("铭文确认器主身份，使礼器与春秋政治网络相互印证。"),
			TEXT("春秋晚期"), TEXT("楚国礼器"), TEXT("比较本页与西周重器的形体变化"), Vermilion,
			Cube, ArtifactTransform(FVector(0, 0, 66), FRotator(0, -42, 0), FVector(1.28f, 1.28f, 1.28f)), 8.0f)
	}));

	Chapters.Add(MakeChapter(TEXT("warring_states"), TEXT("第五章"), TEXT("战国"), TEXT("礼乐、错金银与生活器用展现多元世界。"), {
		MakePage(TEXT("warring_bells"), TEXT("金声玉振"), TEXT("曾侯乙编钟"),
			TEXT("曾侯乙编钟构成规模宏大的礼乐系统，一钟双音体现精确声学设计。"),
			TEXT("钟体铭文还保存了战国时期各地律名与音乐交流信息。"),
			TEXT("战国早期"), TEXT("曾侯乙墓"), TEXT("用横向占位器想象成组编钟"), Gold,
			Cylinder, ArtifactTransform(FVector(0, 0, 62), FRotator(0, 0, 90), FVector(0.72f, 0.72f, 2.0f)), 6.0f),
		MakePage(TEXT("warring_inlay_vessel"), TEXT("华丽工艺"), TEXT("错金银铜壶"),
			TEXT("金银丝片嵌入铜器表面，形成宴饮、狩猎与几何纹样的精细画面。"),
			TEXT("战国工匠以金属色差和复杂构图拓展了青铜器的视觉语言。"),
			TEXT("战国时期"), TEXT("错金银工艺"), TEXT("观察球形占位器的连续表面"), Ink,
			Sphere, ArtifactTransform(FVector(0, 0, 64), FRotator(0, 35, 8), FVector(1.28f, 1.28f, 1.58f)), 14.0f)
	}));

	Chapters.Add(MakeChapter(TEXT("qin_han"), TEXT("第六章"), TEXT("秦汉"), TEXT("帝国尺度、实用器与写实造型开启新篇。"), {
		MakePage(TEXT("qin_chariot"), TEXT("帝国仪仗"), TEXT("秦陵铜车马"),
			TEXT("秦陵铜车马以接近真实结构的车辆、马匹与御者再现帝国仪仗。"),
			TEXT("铸造、焊接、嵌接和彩绘共同完成了高度复杂的青铜模型。"),
			TEXT("秦代"), TEXT("秦始皇帝陵"), TEXT("观察横向占位器的车辆尺度"), Bronze,
			Cube, ArtifactTransform(FVector(0, 0, 48), FRotator(0, -18, 0), FVector(2.1f, 0.78f, 0.82f)), 5.0f),
		MakePage(TEXT("han_changxin_lamp"), TEXT("生活与巧思"), TEXT("长信宫灯"),
			TEXT("长信宫灯将人物造型、照明功能和烟尘导流结构结合，体现汉代生活设计。"),
			TEXT("可拆卸构件便于清理维护，也让器物成为早期环保理念的生动案例。"),
			TEXT("西汉"), TEXT("中山靖王墓"), TEXT("观察人物灯具占位器的立姿"), Gold,
			Cone, ArtifactTransform(FVector(0, 0, 70), FRotator(0, 22, 0), FVector(0.95f, 0.95f, 1.95f)), 10.0f),
		MakePage(TEXT("han_flying_horse"), TEXT("速度定格"), TEXT("铜奔马"),
			TEXT("铜奔马以一足踏飞鸟的构图表现疾驰瞬间，兼具力学平衡与艺术想象。"),
			TEXT("从礼制重器到写实雕塑，青铜在秦汉继续进入更广阔的社会生活。"),
			TEXT("东汉"), TEXT("武威雷台汉墓"), TEXT("按 F8 切换 Tobii 模拟并完成时代巡礼"), Jade,
			Sphere, ArtifactTransform(FVector(0, 0, 72), FRotator(-12, -35, 18), FVector(1.65f, 0.68f, 1.05f)), 16.0f)
	}));
}

void ABronzeExhibitHost::ResolveOrSpawnStage()
{
	if (IsValid(ArtifactStage))
	{
		return;
	}

	if (!ArtifactStageTag.IsNone())
	{
		TArray<AActor*> TaggedActors;
		UGameplayStatics::GetAllActorsWithTag(this, ArtifactStageTag, TaggedActors);
		for (AActor* Actor : TaggedActors)
		{
			if (ABronzeArtifactStage* Stage = Cast<ABronzeArtifactStage>(Actor))
			{
				ArtifactStage = Stage;
				return;
			}
		}
	}

	for (TActorIterator<ABronzeArtifactStage> It(GetWorld()); It; ++It)
	{
		ArtifactStage = *It;
		return;
	}

	if (bSpawnStageIfMissing && GetWorld())
	{
		ArtifactStage = GetWorld()->SpawnActor<ABronzeArtifactStage>(GetActorLocation(), GetActorRotation());
		if (ArtifactStage && !ArtifactStageTag.IsNone())
		{
			ArtifactStage->Tags.AddUnique(ArtifactStageTag);
		}
	}
}

void ABronzeExhibitHost::CreateRuntimeWidget()
{
	if (!WidgetClass)
	{
		return;
	}

	APlayerController* PlayerController = UGameplayStatics::GetPlayerController(this, 0);
	RuntimeWidget = CreateWidget<UBronzeExhibitWidget>(PlayerController, WidgetClass);
	if (!RuntimeWidget)
	{
		return;
	}

	ConfigureRuntimeWidget();

	struct FSetExhibitHostParameters
	{
		ABronzeExhibitHost* Host = nullptr;
	};

	FSetExhibitHostParameters Parameters;
	Parameters.Host = this;
	CallWidgetFunction(TEXT("SetExhibitHost"), &Parameters);
	RuntimeWidget->AddToViewport(WidgetZOrder);

	if (PlayerController)
	{
		PlayerController->bShowMouseCursor = true;
		PlayerController->SetInputMode(FInputModeGameAndUI());
	}
}

void ABronzeExhibitHost::ConfigureRuntimeWidget()
{
	if (!RuntimeWidget)
	{
		return;
	}

	TArray<FBronzeExhibitPage> WidgetPages;
	TArray<FText> NavigationLabels;
	TArray<FName> NavigationIds;
	for (const FBronzeExhibitChapterRecord& Chapter : Chapters)
	{
		NavigationLabels.Add(Chapter.Title);
		NavigationIds.Add(Chapter.ChapterId);

		for (const FBronzeExhibitPageRecord& Page : Chapter.Pages)
		{
			FBronzeExhibitPage WidgetPage;
			WidgetPage.Eyebrow = FText::Format(ExhibitText(TEXT("{0} / {1}")), Chapter.Number, Page.Kicker);
			WidgetPage.Title = Page.Title;
			WidgetPage.Body = FText::Format(ExhibitText(TEXT("{0}\n\n{1}")), Page.Body, Page.Detail);
			WidgetPage.ArchiveCode = FText::Format(ExhibitText(TEXT("{0} | {1}")), Page.Era, Page.Collection);
			WidgetPages.Add(MoveTemp(WidgetPage));
		}
	}

	RuntimeWidget->SetNavigationItems(NavigationLabels, NavigationIds);
	RuntimeWidget->SetPages(WidgetPages, GetCurrentGlobalPageIndex());
	RuntimeWidget->OnPageChanged.AddUniqueDynamic(this, &ABronzeExhibitHost::HandleWidgetPageChanged);
	RuntimeWidget->OnNavigationRequested.AddUniqueDynamic(this, &ABronzeExhibitHost::HandleWidgetNavigationRequested);
}

void ABronzeExhibitHost::UpdateWidgetGaze()
{
	if (!RuntimeWidget)
	{
		return;
	}

	UObject* TobiiSubsystem = ResolveTobiiSubsystem();
	UFunction* Function = TobiiSubsystem ? TobiiSubsystem->FindFunction(TEXT("GetLatestGaze")) : nullptr;
	if (!Function)
	{
		RuntimeWidget->ClearTobiiGaze();
		return;
	}

	TArray<uint8> Parameters;
	Parameters.SetNumZeroed(Function->ParmsSize);
	TobiiSubsystem->ProcessEvent(Function, Parameters.GetData());

	for (TFieldIterator<FStructProperty> It(Function); It; ++It)
	{
		FStructProperty* ReturnProperty = *It;
		if (!ReturnProperty->HasAnyPropertyFlags(CPF_ReturnParm))
		{
			continue;
		}

		void* SampleData = ReturnProperty->ContainerPtrToValuePtr<void>(Parameters.GetData());
		const FStructProperty* DisplayPointProperty = FindFProperty<FStructProperty>(ReturnProperty->Struct, TEXT("DisplayPoint"));
		const FBoolProperty* ValidProperty = FindFProperty<FBoolProperty>(ReturnProperty->Struct, TEXT("bValid"));
		if (DisplayPointProperty && DisplayPointProperty->Struct == TBaseStructure<FVector2D>::Get() && ValidProperty)
		{
			const FVector2D* DisplayPoint = DisplayPointProperty->ContainerPtrToValuePtr<FVector2D>(SampleData);
			const bool bValid = ValidProperty->GetPropertyValue_InContainer(SampleData);
			RuntimeWidget->SubmitTobiiGazeNormalized(*DisplayPoint, bValid, true);
		}
		return;
	}
}

void ABronzeExhibitHost::ApplyCurrentPage(bool bNotifyWidget)
{
	CurrentPageElapsedSeconds = 0.0f;

	FBronzeExhibitPageRecord Page;
	if (!GetCurrentPage(Page))
	{
		if (ArtifactStage)
		{
			ArtifactStage->ClearArtifact();
		}
		return;
	}

	if (ArtifactStage)
	{
		ArtifactStage->ApplyPage(Page);
	}
	UE_LOG(LogTemp, Display, TEXT("BronzeExhibit: showing page %s (%d/%d)."),
		*Page.PageId.ToString(), GetCurrentGlobalPageIndex() + 1, GetTotalPageCount());

	OnPageChanged.Broadcast(CurrentChapterIndex, CurrentPageIndex);
	if (bNotifyWidget)
	{
		if (RuntimeWidget)
		{
			RuntimeWidget->SetPage(GetCurrentGlobalPageIndex(), false);
		}
		CallWidgetFunction(TEXT("HandleExhibitPageChanged"));
	}
}

void ABronzeExhibitHost::SetState(EBronzeExhibitState NewState)
{
	if (State == NewState)
	{
		return;
	}

	State = NewState;
	OnStateChanged.Broadcast(State);
	CallWidgetFunction(TEXT("HandleExhibitStateChanged"));
}

void ABronzeExhibitHost::AdvancePage(bool bForward, bool bManualNavigation)
{
	if (GetTotalPageCount() == 0 || !Chapters.IsValidIndex(CurrentChapterIndex))
	{
		return;
	}

	if (bManualNavigation && bPauseAutoPlayOnManualNavigation && State == EBronzeExhibitState::AutoPlaying)
	{
		SetState(EBronzeExhibitState::Paused);
	}

	int32 ChapterIndex = CurrentChapterIndex;
	int32 PageIndex = CurrentPageIndex + (bForward ? 1 : -1);

	if (bForward)
	{
		while (Chapters.IsValidIndex(ChapterIndex) && PageIndex >= Chapters[ChapterIndex].Pages.Num())
		{
			++ChapterIndex;
			PageIndex = 0;
		}

		if (!Chapters.IsValidIndex(ChapterIndex))
		{
			if (!bLoopAutoPlay && !bManualNavigation)
			{
				SetState(EBronzeExhibitState::Finished);
				return;
			}
			ChapterIndex = 0;
			PageIndex = 0;
		}
	}
	else
	{
		while (ChapterIndex >= 0 && PageIndex < 0)
		{
			--ChapterIndex;
			PageIndex = Chapters.IsValidIndex(ChapterIndex) ? Chapters[ChapterIndex].Pages.Num() - 1 : INDEX_NONE;
		}

		if (!Chapters.IsValidIndex(ChapterIndex))
		{
			ChapterIndex = Chapters.Num() - 1;
			PageIndex = Chapters[ChapterIndex].Pages.Num() - 1;
		}
	}

	CurrentChapterIndex = ChapterIndex;
	CurrentPageIndex = PageIndex;
	ApplyCurrentPage(true);
}

float ABronzeExhibitHost::GetCurrentPageDuration() const
{
	if (Chapters.IsValidIndex(CurrentChapterIndex) && Chapters[CurrentChapterIndex].Pages.IsValidIndex(CurrentPageIndex))
	{
		return FMath::Max(1.0f, Chapters[CurrentChapterIndex].Pages[CurrentPageIndex].AutoAdvanceSeconds);
	}
	return FMath::Max(1.0f, DefaultAutoAdvanceSeconds);
}

UObject* ABronzeExhibitHost::ResolveTobiiSubsystem() const
{
	UGameInstance* GameInstance = GetGameInstance();
	if (!GameInstance)
	{
		return nullptr;
	}

	UClass* TobiiClass = FindObject<UClass>(nullptr, TEXT("/Script/TobiiEyeTracker5.TobiiEyeTrackerSubsystem"));
	if (!TobiiClass)
	{
		TobiiClass = LoadObject<UClass>(nullptr, TEXT("/Script/TobiiEyeTracker5.TobiiEyeTrackerSubsystem"));
	}

	return TobiiClass ? GameInstance->GetSubsystemBase(TobiiClass) : nullptr;
}

bool ABronzeExhibitHost::CallBoolFunction(UObject* Target, FName FunctionName, bool bArgument, bool& OutReturnValue) const
{
	if (!Target)
	{
		return false;
	}

	UFunction* Function = Target->FindFunction(FunctionName);
	if (!Function)
	{
		return false;
	}

	TArray<uint8> Parameters;
	Parameters.SetNumZeroed(Function->ParmsSize);
	for (TFieldIterator<FBoolProperty> It(Function); It; ++It)
	{
		FBoolProperty* Property = *It;
		if (Property->HasAnyPropertyFlags(CPF_ReturnParm))
		{
			continue;
		}
		Property->SetPropertyValue_InContainer(Parameters.GetData(), bArgument);
		break;
	}

	Target->ProcessEvent(Function, Parameters.GetData());
	for (TFieldIterator<FBoolProperty> It(Function); It; ++It)
	{
		FBoolProperty* Property = *It;
		if (Property->HasAnyPropertyFlags(CPF_ReturnParm))
		{
			OutReturnValue = Property->GetPropertyValue_InContainer(Parameters.GetData());
			break;
		}
	}
	return true;
}

bool ABronzeExhibitHost::CallBoolGetter(UObject* Target, FName FunctionName, bool& OutReturnValue) const
{
	if (!Target)
	{
		return false;
	}

	UFunction* Function = Target->FindFunction(FunctionName);
	if (!Function)
	{
		return false;
	}

	TArray<uint8> Parameters;
	Parameters.SetNumZeroed(Function->ParmsSize);
	Target->ProcessEvent(Function, Parameters.GetData());
	for (TFieldIterator<FBoolProperty> It(Function); It; ++It)
	{
		FBoolProperty* Property = *It;
		if (Property->HasAnyPropertyFlags(CPF_ReturnParm))
		{
			OutReturnValue = Property->GetPropertyValue_InContainer(Parameters.GetData());
			return true;
		}
	}
	return false;
}

void ABronzeExhibitHost::CallWidgetFunction(FName FunctionName, void* Parameters)
{
	if (!RuntimeWidget)
	{
		return;
	}

	if (UFunction* Function = RuntimeWidget->FindFunction(FunctionName))
	{
		RuntimeWidget->ProcessEvent(Function, Parameters);
	}
}

void ABronzeExhibitHost::HandleWidgetPageChanged(int32 GlobalPageIndex)
{
	SelectGlobalPage(GlobalPageIndex);
}

void ABronzeExhibitHost::HandleWidgetNavigationRequested(FName NavigationId)
{
	for (int32 ChapterIndex = 0; ChapterIndex < Chapters.Num(); ++ChapterIndex)
	{
		if (Chapters[ChapterIndex].ChapterId == NavigationId)
		{
			SelectChapter(ChapterIndex);
			return;
		}
	}
}
