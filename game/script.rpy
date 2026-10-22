# 이 파일에 게임 스크립트를 입력합니다.
# - 스킬 정의: skills.rpy
# - 캐릭터 및 적(유닛) 정의: units.rpy
# - 전투 UI, 모션 및 전투 루프: battle.rpy

# image 문을 사용해 이미지를 정의합니다.
image bgplaceholder = "background.png"

# 게임에서 사용할 캐릭터를 정의합니다.
define perwin = Character(_('페르윈'), color="#5a36ff")

# 여기에서부터 게임이 시작합니다.
label start:
    python:
        """
        설정(클래스 생성 등)
        """
        currentPlayer = Tester()
    scene bgplaceholder with dissolve
    # KILL YOURSELF
    perwin "아아, 테스트 중이야."
    perwin "이름부터 입력하도록."
    python:
        yourself = renpy.input("여기에 입력하면 돼.")
        currentPlayer.name = yourself.strip()

        if currentPlayer.name == "":
            currentPlayer.name = _("테스터")
    perwin "아, 그래. [currentPlayer.name](이)구나."
    perwin "만들기ㅈㄴ귀찮네"
    jump main

label main:
    if currentPlayer.sanity > 0:
        play music "Time2Dream.wav" fadeout 1.0 fadein 1.0
    else:
        play music "Welcome2LiminalWorld.wav" fadeout 1.0 fadein 1.0
    perwin "선택지 놔둘테니까 테스트하셈;"
    menu:
        "전투":
            jump area_battle
        "탈주":
            stop music fadeout 1.0
            return

label area_battle:
    call battle([WilloWisp(), Teruterubozu()])
    $ player_won = _return
    if player_won:
        perwin "야르"
        # 나중에 보상 얻는 시스템 넣을 곳
    else:
        perwin "ㄲㅂ"
        # 나중에 게임오버(패널티/리트라이 등) 처리 넣을 곳
    jump main
