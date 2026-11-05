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
        "[[아르카나: 멈춰버린 회중시계] 시계 태엽을 역방향으로 감아 과거의 통화를 재생한다" if currentPlayer.has_arcana("broken_watch"):
            "회중시계가 공명하며 부스 안의 시간이 역류합니다! 잊혀진 접속자가 남긴 온전한 물결 데이터가 흘러나옵니다."
            $ currentPlayer.dream_shard += 100
            "{color=#c184ff}[[아르카나 연동 결과]{/color} 꿈의 파편 +100개를 얻고 상급 물결이 공명합니다!"
            call grant_wave_reward("elite", title_text="과거의 통화 기록 — 상급 물결 선택")

        "[[테스터 전용] 공중전화의 내부 회로를 해킹해 발신지를 역추적한다" if currentPlayer.id == "tester":
            "당신은 능숙하게 단말기 패널을 뜯어내고 흐르는 꿈 데이터를 디버깅하기 시작했습니다."
            "신호 너머에는 누군가가 흘리고 간 고순도의 기억 데이터와 물결이 뭉쳐 있었습니다!"
            $ currentPlayer.dream_shard += 80
            "{color=#c184ff}[[테스터 고유 결과]{/color} 꿈의 파편 +80개를 획득하고 물결을 추출합니다!"
            call grant_wave_reward("normal", title_text="회로 역추적 — 물결 선택")

        "{color=#cc1100}[[광기 선택지] 수화기에 귀를 밀착하고 기괴한 백색소음을 끝까지 받아들인다 (이성치 0 이하){/color}" if currentPlayer.sanity <= 0:
            "수화기 너머에서 수많은 사람들의 비명과 속삭임이 뇌수로 직접 흘러들어옵니다."
            "정신이 찢어질 듯 아파오지만, 그 속에서 악몽을 다루는 금기된 물결을 깨우칩니다!"
            $ currentPlayer.take_sanity(15)
            "{color=#cc1100}[[광기 결과]{/color} 이성치가 15 감소한 대신 침식된 물결을 흡수합니다!"
            call grant_wave_reward("eroded", title_text="백색소음의 계시 — 침식 물결 선택")

        "조심스럽게 수화기를 들어 응답한다":
            "수화기를 들자 익숙하고도 차분한 멜로디가 흘러나오며 긴장되었던 마음이 가라앉습니다."
            $ currentPlayer.heal(35)
            $ currentPlayer.recover_sanity(20)
            "정신력을 35 회복하고, 이성치를 +20 회복했습니다."

        "불길한 기운을 느끼고 부스 유리를 부숴 파편만 챙긴다":
            "부스를 가격하자 유리 대신 응결된 꿈의 파편들이 쏟아져 나왔지만, 불쾌한 이명이 귓가를 스칩니다."
            $ currentPlayer.dream_shard += 90
            $ currentPlayer.take_sanity(15)
            "꿈의 파편 +90개를 획득하고, 이성치가 15 감소했습니다."
    return


# ==============================================================================
# [일반 사건 2] 거울 회랑의 투영
# ==============================================================================
label event_mirror_corridor:
    "— {color=#c184ff}[[사건] 거울 회랑의 투영{/color} —"
    "끝없이 이어진 거울 복도를 걷던 중, 거울 속의 당신이 반 박자 늦게 움직이고 있다는 사실을 깨닫습니다."
    "거울 너머의 '나'가 미소를 지으며 손을 내밉니다."

    menu:
        "[[테스터 전용] 거울의 반사 지연 버그(Lag)를 이용해 보유한 물결을 복제·강화한다" if currentPlayer.id == "tester":
            "거울이 당신의 움직임을 따라잡기 전에 역으로 거울 속의 연산력을 흡수했습니다!"
            $ currentPlayer.heal(25)
            call screen wave_upgrade_ui(cost_per_upgrade=0)
            $ up_w = _return
            if isinstance(up_w, Wave):
                $ currentPlayer.upgrade_wave(up_w)
                "{color=#c184ff}[[테스터 고유 결과]{/color} 정신력을 25 회복하고 물결 {color=#5ce1e6}[up_w.display_name]{/color}[tossi.pick(up_w.display_name, u'을')] 강화했습니다!"
            else:
                $ currentPlayer.dream_shard += 90
                "{color=#c184ff}[[테스터 고유 결과]{/color} 정신력을 25 회복하고 꿈의 파편 +90개를 얻었습니다!"

        "거울 속의 나와 마주 손을 맞잡고 내면의 대화를 나눈다":
            "거울의 차가운 감촉과 함께 흐트러졌던 자아의 경계가 선명해집니다."
            $ currentPlayer.recover_sanity(25)
            $ currentPlayer.heal(25)
            call grant_wave_reward("normal", preferred_path="clarity", title_text="내면의 대화 — 청명 물결 공명")

        "거울 속의 나를 강하게 후려쳐 박살 낸다":
            "쨍그랑! 거울이 산산조각 나며 거울 너머에 숨겨져 있던 기묘한 유물이 바닥으로 굴러떨어집니다."
            "하지만 거울 속의 자신이 흘린 피가 당신의 손등에도 맺혀 있습니다."
            $ currentPlayer.harm(18)
            $ currentPlayer.take_sanity(20)
            "정신력을 18, 이성치를 20 잃은 대신 거울 너머의 아르카나를 발견했습니다!"
            call grant_arcana_reward(3, include_cursed=True, title_text="깨진 거울의 유물 — 아르카나 선택")
    return


# ==============================================================================
# [일반 사건 3] 얼굴 없는 자동판매기
# ==============================================================================
label event_vending_machine:
    "— {color=#c184ff}[[사건] 얼굴 없는 자동판매기{/color} —"
    "아무것도 없는 허공에 보랏빛 네온사인을 깜빡이는 자동판매기가 서 있습니다."
    "진열창에는 라벨이 붙지 않은 캔들이 줄지어 놓여 있습니다."

    menu:
        "[[아르카나: 페르윈의 해킹 동글] 자판기 결제 단자에 동글을 꽂아 관리자 모드를 연다" if currentPlayer.has_arcana("perwin_dongle"):
            "자판기가 삑— 소리를 내며 모든 잠금장치를 해제합니다!"
            $ currentPlayer.mp = currentPlayer.max_mp
            "정신력이 완전히 회복되고 자판기 깊숙이 보관되어 있던 물결 캡슐이 배출됩니다!"
            call grant_wave_reward("elite", title_text="관리자 모드 개방 — 상급 물결 선택")

        "[[파편 50개 소모] 정체불명의 보랏빛 캔을 뽑아 마신다" if currentPlayer.dream_shard >= 50:
            $ currentPlayer.dream_shard -= 50
            $ currentPlayer.mp = currentPlayer.max_mp
            "톡 쏘는 청량감이 뇌를 관통합니다! 정신력이 완전히 회복되고 새로운 물결이 깨어납니다."
            call grant_wave_reward("normal", title_text="보랏빛 음료의 각성 — 물결 선택")

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
                    "몰려온 악몽을 해치우고 자판기 내부의 꿈의 파편 110개와 물결을 회수했습니다!"
                    call grant_wave_reward("normal")

        "수상한 기계에는 손을 대지 않고 지나간다":
            $ currentPlayer.recover_sanity(10)
            "신중한 판단으로 이성치를 +10 회복했습니다."
    return


# ==============================================================================
# [침식된 사건 1] 맥동하는 신경 단말기 (이성치 0 이하 전용)
# ==============================================================================
label event_eroded_flesh_terminal:
    "— {color=#cc1100}[[침식된 사건] 맥동하는 신경 단말기{/color} —"
    "이성이 무너진 시야 너머로, 차가운 기계였던 터미널이 살아 숨 쉬는 붉은 신경 다발처럼 꿈틀거리고 있습니다."
    "단말기의 케이블이 뱀처럼 기어 와 당신의 목덜미에 접속을 시도합니다."

    menu:
        "{color=#cc1100}[[신경 직결] 저항하지 않고 단말기와 뇌파를 직접 동기화한다 (정신력 25 소모){/color}":
            $ currentPlayer.harm(25)
            "타들어 가는 고통과 함께 금기된 전투 연산 데이터가 뇌에 각인됩니다!"
            call grant_wave_reward("elite", preferred_path="rupture", title_text="신경 직결 — 상급 파열 물결 공명")

        "{color=#cc1100}[[기억 포식] 단말기 안의 뒤틀린 기억들을 강제로 집어삼킨다 (이성치 -25){/color}":
            $ currentPlayer.take_sanity(25)
            $ currentPlayer.heal(40)
            "타인의 악몽을 통째로 삼키자 정신력이 회복되며 단말기 코어에서 기물이 튀어나옵니다!"
            call grant_arcana_reward(3, include_cursed=True, title_text="기억 포식 — 아르카나(기물) 획득")

        "케이블을 쳐내고 강제로 회로를 차단한다":
            $ currentPlayer.recover_sanity(30)
            "거친 숨을 몰아쉬며 환각에서 벗어났습니다. 이성치를 +30 회복했습니다."
    return


# ==============================================================================
# [침식된 사건 2] 속삭이는 심연의 우물 (이성치 0 이하 전용)
# ==============================================================================
label event_eroded_whispering_well:
    "— {color=#cc1100}[[침식된 사건] 속삭이는 심연의 우물{/color} —"
    "바닥이 보이지 않는 검은 우물 속에서 당신의 목소리와 똑같은 소리가 흘러나옵니다."
    "『더 깊이 내려오고 싶다면, 네가 가진 조각을 던져 넣어라…』"

    menu:
        "{color=#cc1100}우물 속으로 몸을 기울여 심연의 정수를 마신다 (이성치 -20){/color}":
            $ currentPlayer.take_sanity(20)
            "얼음장처럼 차가운 액체가 목을 타고 넘어가며 심연의 물결이 요동칩니다!"
            call grant_wave_reward("elite", preferred_path="erosion", title_text="심연의 정수 — 상급 잠식 물결 공명")

        "{color=#cc1100}[[파편 100개 투척] 꿈의 파편을 우물에 바친다{/color}" if currentPlayer.dream_shard >= 100:
            $ currentPlayer.dream_shard -= 100
            $ currentPlayer.mp = currentPlayer.max_mp
            "우물 속에서 검은 빛기둥이 솟구치며 정신력을 완전히 회복시키고 유물 하나를 떠올립니다!"
            call grant_arcana_reward(3, include_cursed=True, title_text="심연의 우물 — 아르카나 선택")

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
    "문장은 거기서 끊겨 있고, 콘솔 내부에서 순도 높은 결정과 유물이 흘러나옵니다."

    python:
        if playerAccount.story_progress < 1:
            playerAccount.story_progress = 1
        currentPlayer.dream_shard += 80
        currentPlayer.heal(30)

    "기억의 핵을 회수하여 {color=#c184ff}꿈의 파편 +80개{/color}를 얻고 정신력을 30 회복했습니다!"
    call grant_arcana_reward(3, include_cursed=True, title_text="제1차원 기억의 핵 — 아르카나(기물) 획득")
    return


label event_core_dim2:
    "— {color=#c184ff}[[심층 사건 · 제2차원 기억의 핵] 가라앉은 거리와 첫 번째 피험자{/color} —"
    "심층몽의 무너진 시계탑 아래, 굳어버린 기억의 결정체를 마주합니다."
    rinat "이 파형은… 인간의 꿈과 몽마의 마력이 뒤섞여 있어. 아주 오래전에 누군가 인위적으로 이 심층에 닻을 내렸던 흔적이야."
    perwin "…리나트, 저 결정 안에 기록된 뇌파 패턴을 봐. 지금 접속 중인 [tossi.postfix(currentPlayer.name, u'과')] 동기화율이 99.8%% 일치해."

    menu:
        "결정체에 손을 대어 기억의 물결을 완전히 흡수한다 (정신력 40 회복 + 상급 물결 획득)":
            $ currentPlayer.heal(40)
            "잊고 있었던 기시감이 머릿속을 스치며 강한 물결이 깨어납니다!"
            call grant_wave_reward("elite", title_text="제2차원 기억의 핵 — 상급 물결 선택")
        "결정체 내부의 유물을 추출하고 이성을 다잡는다 (이성치 +30 회복 + 아르카나 획득)":
            $ currentPlayer.recover_sanity(30)
            "냉정하게 기록을 백업하고 결정 속의 유물을 회수했습니다."
            call grant_arcana_reward(3, include_cursed=True, title_text="제2차원 기억의 핵 — 아르카나 선택")

    python:
        if playerAccount.story_progress < 2:
            playerAccount.story_progress = 2
        currentPlayer.dream_shard += 100
    return


label event_core_dim3:
    "— {color=#c184ff}[[심층 사건 · 제3차원 기억의 핵] 허수의 바다 밑바닥{/color} —"
    "모든 꿈이 흘러들어 오는 허수의 바다 중심부. 그곳에는 거대한 빛의 소용돌이가 고요히 회전하고 있습니다."
    perwin "드디어 도착했군… 여기가 모든 꿈의 기원, 헤우니스탄(XEWNISTAN)의 심장부야."
    rinat "하지만 조심해! 바로 앞 구역의 중계소를 지나면, 이 심연 자체를 지키는 마지막 주인 악몽이 기다리고 있어."

    python:
        if playerAccount.story_progress < 3:
            playerAccount.story_progress = 3
        currentPlayer.heal(50)

    "심연의 중심부와 공명하여 정신력을 50 회복하고 최상급 물결을 각성합니다!"
    call grant_wave_reward("boss", title_text="제3차원 기억의 핵 — 심연의 물결 선택")
    return