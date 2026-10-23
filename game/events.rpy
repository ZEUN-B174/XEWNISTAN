# 사건(Event) 구역 관리 및 비주얼 노벨 이벤트 스크립트
# - 일반 사건 ("normal"): 랜덤 풀에서 등장, 캐릭터 고유 선택지 / 이성치 조건부 선택지 포함
# - 침식된 사건 ("eroded"): 이성치 0 이하일 때 변질된 사건 구역에서 등장하는 기괴한 고위험·고보상 사건
# - 심층 사건 ("core"): 각 차원의 6구역(기억의 핵)에 고정 배치되는 메인 스토리 사건

init 3 python:
    import random
    from dataclasses import dataclass

    @dataclass
    class DreamEvent:
        id: str
        title: str
        label_name: str
        event_type: str = "normal"  # "normal" / "eroded" / "core"
        target_dim: int = 0         # 0이면 전 차원 공용, 1~3이면 특정 차원 전용

    EVENT_REGISTRY = [
        # 일반 사건 풀
        DreamEvent("payphone", _("무인 역의 공중전화"), "event_payphone", "normal", 0),
        DreamEvent("mirror_corridor", _("거울 회랑의 투영"), "event_mirror_corridor", "normal", 0),
        DreamEvent("vending_machine", _("얼굴 없는 자동판매기"), "event_vending_machine", "normal", 0),

        # 침식된 사건 풀 (이성치 0 이하 시 등장)
        DreamEvent("flesh_terminal", _("맥동하는 신경 단말기"), "event_eroded_flesh_terminal", "eroded", 0),
        DreamEvent("whispering_well", _("속삭이는 심연의 우물"), "event_eroded_whispering_well", "eroded", 0),

        # 차원별 6구역 고정 심층 사건 (메인 스토리 뼈대)
        DreamEvent("core_dim1", _("기억의 핵 I : 잔류하는 로그인 기록"), "event_core_dim1", "core", 1),
        DreamEvent("core_dim2", _("기억의 핵 II : 가라앉은 거리와 첫 번째 피험자"), "event_core_dim2", "core", 2),
        DreamEvent("core_dim3", _("기억의 핵 III : 허수의 바다 밑바닥"), "event_core_dim3", "core", 3),
    ]

    def pick_dream_event(event_type, dim, visited_list):
        if event_type == "core":
            for ev in EVENT_REGISTRY:
                if ev.event_type == "core" and ev.target_dim == dim:
                    return ev

        candidates = [
            ev for ev in EVENT_REGISTRY
            if ev.event_type == event_type
            and (ev.target_dim == 0 or ev.target_dim == dim)
            and ev.id not in visited_list
        ]
        # 만약 이번 런에서 해당 타입의 사건을 모두 봤다면 중복 허용으로 폴백
        if not candidates:
            candidates = [
                ev for ev in EVENT_REGISTRY
                if ev.event_type == event_type
                and (ev.target_dim == 0 or ev.target_dim == dim)
            ]
        return random.choice(candidates)


label node_event(event_type="normal"):
    python:
        chosen_ev = pick_dream_event(event_type, currentDim, visitedEvents)
        if chosen_ev.id not in visitedEvents:
            visitedEvents.append(chosen_ev.id)

    $ renpy.call(chosen_ev.label_name)
    return


# ==============================================================================
# [일반 사건 1] 무인 역의 공중전화
# ==============================================================================
label event_payphone:
    "— {color=#c184ff}[[사건] 무인 역의 공중전화{/color} —"
    "안개 낀 기차역 플랫폼 한가운데, 낡은 공중전화 부스 하나가 덩그러니 서 있습니다."
    "선도 연결되어 있지 않은 전화기에서 요란한 벨 소리가 울려 퍼집니다."

    menu:
        "[[테스터 전용] 공중전화의 내부 회로를 해킹해 발신지를 역추적한다" if currentPlayer.id == "tester":
            "당신은 능숙하게 단말기 패널을 뜯어내고 흐르는 꿈 데이터를 디버깅하기 시작했습니다."
            "신호 너머에는 누군가가 흘리고 간 고순도의 기억 데이터와 파편이 뭉쳐 있었습니다!"
            $ currentPlayer.dream_shard += 110
            $ currentPlayer.atk += 3
            "{color=#c184ff}[[테스터 고유 결과]{/color} 꿈의 파편 +110개를 획득하고, 공격력이 +3 상승했습니다!"

        "{color=#cc1100}[[광기 선택지] 수화기에 귀를 밀착하고 기괴한 백색소음을 끝까지 받아들인다 (이성치 0 이하){/color}" if currentPlayer.sanity <= 0:
            "수화기 너머에서 수많은 사람들의 비명과 속삭임이 뇌수로 직접 흘러들어옵니다."
            "정신이 찢어질 듯 아파오지만, 그 속에서 악몽을 다루는 금기된 감각을 깨우칩니다!"
            $ currentPlayer.take_sanity(15)
            $ currentPlayer.atk += 5
            $ currentPlayer.crit_chance += 10
            "{color=#ff4444}[[광기 결과]{/color} 이성치가 15 감소한 대신, 공격력 +5 및 치명타 확률 +10%%를 얻었습니다!"

        "조심스럽게 수화기를 들어 응답한다":
            "수화기를 들자 익숙하고도 차분한 멜로디가 흘러나오며 긴장되었던 마음이 가라앉습니다."
            $ currentPlayer.heal(30)
            $ currentPlayer.recover_sanity(15)
            "정신력을 30 회복하고, 이성치를 +15 회복했습니다."

        "불길한 기운을 느끼고 부스 유리를 부숴 파편만 챙긴다":
            "부스를 가격하자 유리 대신 응결된 꿈의 파편들이 쏟아져 나왔지만, 불쾌한 이명이 귓가를 스칩니다."
            $ currentPlayer.dream_shard += 80
            $ currentPlayer.take_sanity(15)
            "꿈의 파편 +80개를 획득하고, 이성치가 15 감소했습니다."
    return


# ==============================================================================
# [일반 사건 2] 거울 회랑의 투영
# ==============================================================================
label event_mirror_corridor:
    "— {color=#c184ff}[[사건] 거울 회랑의 투영{/color} —"
    "끝없이 이어진 거울 복도를 걷던 중, 거울 속의 당신이 반 박자 늦게 움직이고 있다는 사실을 깨닫습니다."
    "거울 너머의 '나'가 미소를 지으며 손을 내밉니다."

    menu:
        "[[테스터 전용] 거울의 반사 지연 버그(Lag)를 이용해 자신의 전투 데이터를 복제한다" if currentPlayer.id == "tester":
            "거울이 당신의 움직임을 따라잡기 전에 역으로 거울 속의 연산력을 흡수했습니다!"
            $ currentPlayer.max_mp += 25
            $ currentPlayer.heal(25)
            $ currentPlayer.defence += 4
            "{color=#c184ff}[[테스터 고유 결과]{/color} 최대 정신력 +25(및 회복), 방어력 +4가 상승했습니다!"

        "거울 속의 나와 마주 손을 맞잡고 내면의 대화를 나눈다":
            "거울의 차가운 감촉과 함께 흐트러졌던 자아의 경계가 선명해집니다."
            $ currentPlayer.recover_sanity(25)
            $ currentPlayer.heal(20)
            "이성치를 +25 회복하고, 정신력을 20 회복했습니다."

        "거울 속의 나를 강하게 후려쳐 박살 낸다":
            "쨍그랑! 거울이 산산조각 나며 날카로운 꿈의 결정 파편들이 바닥에 흩어집니다."
            "하지만 거울 속의 자신이 흘린 피가 당신의 손등에도 맺혀 있습니다."
            $ currentPlayer.harm(15)
            $ currentPlayer.take_sanity(20)
            $ currentPlayer.dream_shard += 130
            $ currentPlayer.atk += 3
            "정신력을 15, 이성치를 20 잃은 대신 꿈의 파편 +130개와 공격력 +3을 얻었습니다!"
    return


# ==============================================================================
# [일반 사건 3] 얼굴 없는 자동판매기
# ==============================================================================
label event_vending_machine:
    "— {color=#c184ff}[[사건] 얼굴 없는 자동판매기{/color} —"
    "아무것도 없는 허공에 보랏빛 네온사인을 깜빡이는 자동판매기가 서 있습니다."
    "진열창에는 라벨이 붙지 않은 캔들이 줄지어 놓여 있습니다."

    menu:
        "[[파편 50개 소모] 정체불명의 보랏빛 캔을 뽑아 마신다" if currentPlayer.dream_shard >= 50:
            $ currentPlayer.dream_shard -= 50
            $ currentPlayer.mp = currentPlayer.max_mp
            $ currentPlayer.atk += 2
            "톡 쏘는 청량감이 뇌를 관통합니다! 정신력이 완전히 회복되고 공격력이 +2 상승했습니다."

        "돈을 넣지 않고 기계 아랫부분을 힘껏 걷어찬다":
            $ luck = random.randint(1, 100)
            if luck <= 60:
                "덜컹거리는 소리와 함께 배출구로 꿈의 파편들이 우르르 쏟아져 나왔습니다!"
                $ currentPlayer.dream_shard += 90
                "꿈의 파편 +90개를 공짜로 챙겼습니다!"
            else:
                "기계가 기괴한 경보음을 울리며 주변의 악몽을 불러들였습니다!"
                $ enemies = build_battle_enemies(currentDim, "normal")
                call battle(enemies, phase_count=1)
                $ won = _return
                if won:
                    $ play_exploration_bgm(currentDim, currentPlayer.sanity)
                    $ currentPlayer.dream_shard += 110
                    "몰려온 악몽을 해치우고 자판기 내부의 꿈의 파편 110개를 회수했습니다!"

        "수상한 기계에는 손을 대지 않고 지나간다":
            $ currentPlayer.recover_sanity(10)
            "신중한 판단으로 이성치를 +10 회복했습니다."
    return


# ==============================================================================
# [침식된 사건 1] 맥동하는 신경 단말기 (이성치 0 이하 전용)
# ==============================================================================
label event_eroded_flesh_terminal:
    "— {color=#ff4444}[[침식된 사건] 맥동하는 신경 단말기{/color} —"
    "이성이 무너진 시야 너머로, 차가운 기계였던 터미널이 살아 숨 쉬는 붉은 신경 다발처럼 꿈틀거리고 있습니다."
    "단말기의 케이블이 뱀처럼 기어 와 당신의 목덜미에 접속을 시도합니다."

    menu:
        "{color=#cc1100}[[신경 직결] 저항하지 않고 단말기와 뇌파를 직접 동기화한다 (정신력 25 소모){/color}":
            $ currentPlayer.harm(25)
            $ currentPlayer.atk += 6
            $ currentPlayer.crit_damage = round(currentPlayer.crit_damage + 0.25, 2)
            "타들어 가는 고통과 함께 금기된 전투 연산 데이터가 뇌에 각인됩니다!"
            "{color=#ff4444}[[침식 보상]{/color} 정신력을 25 소모하고 공격력 +6, 치명타 피해 +0.25배를 획득했습니다!"

        "{color=#cc1100}[[기억 포식] 단말기 안의 뒤틀린 기억들을 강제로 집어삼킨다 (이성치 -25){/color}":
            $ currentPlayer.take_sanity(25)
            $ currentPlayer.max_mp += 35
            $ currentPlayer.heal(50)
            $ currentPlayer.dream_shard += 120
            "타인의 악몽을 통째로 삼키자 정신력이 기괴하게 부풀어 오릅니다!"
            "{color=#ff4444}[[침식 보상]{/color} 최대 정신력 +35, 정신력 +50 회복, 꿈의 파편 +120개를 획득했습니다!"

        "케이블을 쳐내고 강제로 회로를 차단한다":
            $ currentPlayer.recover_sanity(30)
            "거친 숨을 몰아쉬며 환각에서 벗어났습니다. 이성치를 +30 회복했습니다."
    return


# ==============================================================================
# [침식된 사건 2] 속삭이는 심연의 우물 (이성치 0 이하 전용)
# ==============================================================================
label event_eroded_whispering_well:
    "— {color=#ff4444}[[침식된 사건] 속삭이는 심연의 우물{/color} —"
    "바닥이 보이지 않는 검은 우물 속에서 당신의 목소리와 똑같은 소리가 흘러나옵니다."
    "『더 깊이 내려오고 싶다면, 네가 가진 조각을 던져 넣어라…』"

    menu:
        "{color=#cc1100}우물 속으로 몸을 기울여 심연의 정수를 마신다 (이성치 -20){/color}":
            $ currentPlayer.take_sanity(20)
            $ currentPlayer.atk += 5
            $ currentPlayer.defence += 5
            "얼음장처럼 차가운 액체가 목을 타고 넘어가며 모든 감각이 예리해집니다! (공격력 +5, 방어력 +5)"

        "{color=#cc1100}[[파편 100개 투척] 꿈의 파편을 우물에 바친다{/color}" if currentPlayer.dream_shard >= 100:
            $ currentPlayer.dream_shard -= 100
            $ currentPlayer.max_mp += 40
            $ currentPlayer.mp = currentPlayer.max_mp
            $ currentPlayer.atk += 4
            "우물 속에서 검은 빛기둥이 솟구치며 당신의 정신력을 완벽하게 재구축했습니다! (최대 정신력 +40, 정신력 완전 회복, 공격력 +4)"

        "우물을 봉인하고 발걸음을 돌린다":
            $ currentPlayer.recover_sanity(20)
            $ currentPlayer.dream_shard += 50
            "우물 주변에 떨어진 파편 50개만 줍고 자리를 떴습니다. (이성치 +20 회복)"
    return


# ==============================================================================
# [심층 사건 (6구역 고정 노드)] 차원별 메인 스토리 뼈대
# ==============================================================================
label event_core_dim1:
    "— {color=#c184ff}[[심층 사건 · 제1차원 기억의 핵] 잔류하는 로그인 기록{/color} —"
    "표층몽의 가장 깊은 곳에서, 꿈세계의 풍경과는 이질적인 홀로그램 콘솔 하나를 발견했습니다."
    perwin "잠깐, 저 콘솔의 시리얼 넘버… 우리가 드림링크를 개발할 때 폐기했던 초기 프로토타입의 흔적이야!"
    rinat "이상하네, 분명 초기 버전에서는 아무도 이 깊이까지 접속한 적이 없었을 텐데…?"
    "콘솔 화면에는 알 수 없는 접속자의 마지막 로그가 깜빡이고 있습니다.\n『경고: 악몽은 외부에서 침입한 바이러스가 아니다. 이곳에 모인 사람들의 무의식이 스스로를 방어하기 위해 만들어낸…』"
    "문장은 거기서 끊겨 있고, 콘솔 내부에서 순도 높은 결정이 흘러나옵니다."

    python:
        if playerAccount.story_progress < 1:
            playerAccount.story_progress = 1
        currentPlayer.dream_shard += 100
        currentPlayer.max_mp += 20
        currentPlayer.heal(30)

    "기억의 핵을 회수하여 {color=#c184ff}꿈의 파편 +100개{/color}, {color=#c184ff}최대 정신력 +20{/color}을 얻고 정신력을 30 회복했습니다!"
    return


label event_core_dim2:
    "— {color=#c184ff}[[심층 사건 · 제2차원 기억의 핵] 가라앉은 거리와 첫 번째 피험자{/color} —"
    "심층몽의 무너진 시계탑 아래, 굳어버린 기억의 결정체를 마주합니다."
    rinat "이 파형은… 인간의 꿈과 몽마의 마력이 뒤섞여 있어. 아주 오래전에 누군가 인위적으로 이 심층에 닻을 내렸던 흔적이야."
    perwin "…리나트, 저 결정 안에 기록된 뇌파 패턴을 봐. 지금 접속 중인 [currentPlayer.name](와)과 동기화율이 99.8%% 일치해."

    menu:
        "결정체에 손을 대어 기억을 완전히 흡수한다 (공격력 +5, 정신력 40 회복)":
            $ currentPlayer.atk += 5
            $ currentPlayer.heal(40)
            "잊고 있었던 기시감이 머릿속을 스치며 강한 힘이 깨어납니다!"
        "이성이 흔들리지 않도록 데이터만 추출한다 (방어력 +5, 이성치 +30 회복)":
            $ currentPlayer.defence += 5
            $ currentPlayer.recover_sanity(30)
            "냉정하게 기록을 백업하고 정신의 균형을 되찾았습니다."

    python:
        if playerAccount.story_progress < 2:
            playerAccount.story_progress = 2
        currentPlayer.dream_shard += 120
    return


label event_core_dim3:
    "— {color=#c184ff}[[심층 사건 · 제3차원 기억의 핵] 허수의 바다 밑바닥{/color} —"
    "모든 꿈이 흘러들어 오는 허수의 바다 중심부. 그곳에는 거대한 빛의 소용돌이가 고요히 회전하고 있습니다."
    perwin "드디어 도착했군… 여기가 모든 꿈의 기원, 헤우니스탄(XEWNISTAN)의 심장부야."
    rinat "하지만 조심해! 바로 앞 구역의 중계소를 지나면, 이 심연 자체를 지키는 마지막 주인 악몽이 기다리고 있어."

    python:
        if playerAccount.story_progress < 3:
            playerAccount.story_progress = 3
        currentPlayer.atk += 6
        currentPlayer.defence += 6
        currentPlayer.heal(50)

    "심연의 중심부와 공명하여 {color=#c184ff}공격력 +6, 방어력 +6{/color}이 상승하고 정신력을 50 회복했습니다!"
    return

