# 이 파일에 게임 스크립트를 입력합니다.
# - 스킬 정의: skills.rpy
# - 캐릭터 및 적(유닛) 정의: units.rpy
# - 전투 UI, 모션 및 전투 루프: battle.rpy
# - 탐사 루프 및 연구실 베이스캠프: exploration.rpy
# - 사건(Event) 및 심층 스토리: events.rpy

# image 문을 사용해 이미지를 정의합니다.
image bgplaceholder = "background.png"

# 게임에서 사용할 캐릭터를 정의합니다.
define perwin = Character(_('페르윈'), color="#5a36ff")
define rinat = Character(_('리나트'), color="#ff66b2")

# 여기에서부터 게임이 시작합니다.
label start:
    python:
        """
        설정(클래스 생성 등)
        """
        playerAccount = Player()
        currentPlayer = Tester()
    scene bgplaceholder with dissolve
    # 생각해보니까 이것도 자살을 소재로 한 게임이라고 할 수가 있을ㄲ
    # (사유: 주인공 스킬 및 등장인물(나중에 자살자 캐릭터들이 등장할 예정이라ww))
    perwin "안녕, 베타 테스트 프로그램에 지원해줘서 고마워."
    perwin "테스트에 앞서서 먼저 신분 확인을 할 건데 네 이름을 알려줄래?"
    python:
        yourself = renpy.input("여기에 입력하면 돼.")
        currentPlayer.name = yourself.strip()

        if currentPlayer.name == "":
            currentPlayer.name = _("테스터")
    perwin "음, 그래. [currentPlayer.name]. 확인 완료했어."
    rinat "드림링크 베타 테스트에 온 걸 환영해, [currentPlayer.name]!"
    jump lab_hub