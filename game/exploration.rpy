# 탐사(시뮬레이션 우주 스타일 로그라이트 루프) 및 연구실 베이스캠프 시스템
# - 3개 차원(Dim 1~3) x 8개 구역(Area 1~8)
# - 차원 진입 시 초기/계층 보너스 선택
# - 1~5구역: 자유 탐사 (이성치 0 이하 시 '침식된 구역' 변질 기믹)
# - 6구역: 심층 사건 (메인 스토리 고정 노드)
# - 7구역: 드림링크 중계소 (페르윈 휴식/조정 & 리나트 상점 고정 노드)
# - 8구역: 차원 보스 (주인 악몽)

default playerAccount = None
default currentDim = 1
default currentArea = 1
default in_dream_run = False
default run_cleared = False
default visitedEvents = []
default next_nodes = []

init 3 python:
    import random
    from dataclasses import dataclass

    MAX_DIM = 3
    MAX_AREA = 8

    DIMENSION_INFO = {
        1: {
            "name": _("표층몽"),
            "subtitle": _("얕은 잠의 가장자리"),
            "mult": 1.0,
            "bgm_normal": "Time2Dream.wav",
            "bgm_insane": "Welcome2LiminalWorld.wav",
            "boss_name": _("표층의 감시자 · 도깨비불 군체 [보스]"),
            "boss_sprite": "willowisp",
        },
        2: {
            "name": _("심층몽"),
            "subtitle": _("가라앉은 무의식의 거리"),
            "mult": 1.4,
            "bgm_normal": "Nightmare Town.wav",
            "bgm_insane": "BackRoom.wav",
            "boss_name": _("심층의 처형인 · 붉은 테루테루보즈 [보스]"),
            "boss_sprite": "teruterubozu",
        },
        3: {
            "name": _("허수의 바다"),
            "subtitle": _("모든 꿈이 집결하는 심연"),
            "mult": 1.9,
            "bgm_normal": "BackRoom.wav",
            "bgm_insane": "Welcome2LiminalWorld.wav",
            "boss_name": _("허수의 파수꾼 · 영점의 망령 [보스]"),
            "boss_sprite": "willowisp",
        },
    }

    @dataclass
    class AreaNode:
        node_type: str      # "battle", "eroded_battle", "elite", "event", "eroded_event", "reward", "eroded_reward", "relay", "core_event", "boss"
        tag: str            # UI 상단 분류 태그
        title: str          # 구역 이름
        desc: str           # 구역 설명
        reward_hint: str    # 예상 보상/특징 안내
        is_eroded: bool = False

    NODE_TEMPLATES = {
        "battle": AreaNode(
            node_type="battle",
            tag=_("[전투]"),
            title=_("악몽 조우"),
            desc=_("배회하는 악몽들을 쓰러뜨리고 길을 개척합니다."),
            reward_hint=_("보상: 꿈의 파편 + 전투 후 공명(강화)"),
            is_eroded=False,
        ),
        "eroded_battle": AreaNode(
            node_type="eroded_battle",
            tag=_("[광란의 전투 · 침식]"),
            title=_("폭주하는 악몽"),
            desc=_("이성 붕괴에 이끌려 흉포해진 악몽 무리가 덮쳐옵니다."),
            reward_hint=_("보상: 다량의 꿈의 파편 + 고효율 공명"),
            is_eroded=True,
        ),
        "elite": AreaNode(
            node_type="elite",
            tag=_("[정예]"),
            title=_("짙은 악몽의 영역"),
            desc=_("강력한 정예 악몽이 도사리고 있는 위험 구역입니다."),
            reward_hint=_("보상: 대량의 꿈의 파편 + 상급 공명(강화)"),
            is_eroded=False,
        ),
        "event": AreaNode(
            node_type="event",
            tag=_("[사건]"),
            title=_("꿈의 단편"),
            desc=_("누군가의 기억과 무의식이 응결된 기묘한 사건을 마주합니다."),
            reward_hint=_("특징: 선택지 분기 (캐릭터 / 이성치 조건)"),
            is_eroded=False,
        ),
        "eroded_event": AreaNode(
            node_type="eroded_event",
            tag=_("[침식된 사건 · 침식]"),
            title=_("악몽의 이면"),
            desc=_("무너진 이성 너머로 꿈세계의 뒤틀린 이면이 모습을 드러냅니다."),
            reward_hint=_("특징: 고위험 · 고보상 광기 사건"),
            is_eroded=True,
        ),
        "reward": AreaNode(
            node_type="reward",
            tag=_("[자각]"),
            title=_("무의식 공명 지점"),
            desc=_("꿈을 자각하여 전투 없이 무의식의 힘을 끌어냅니다."),
            reward_hint=_("보상: 무료 스탯 공명 / 파편 / 이성 조정"),
            is_eroded=False,
        ),
        "eroded_reward": AreaNode(
            node_type="eroded_reward",
            tag=_("[금기된 자각 · 침식]"),
            title=_("심연의 등가교환"),
            desc=_("정신이나 이성을 대가로 금기된 힘을 강제로 추출합니다."),
            reward_hint=_("보상: 대가를 치르는 파격적 강화"),
            is_eroded=True,
        ),
        "relay": AreaNode(
            node_type="relay",
            tag=_("[중계소]"),
            title=_("드림링크 안전지대"),
            desc=_("현실의 페르윈·리나트와 통신이 연결되는 정비 구역입니다."),
            reward_hint=_("특징: 정신력/이성 정비 및 리나트의 상점"),
            is_eroded=False,
        ),
        "core_event": AreaNode(
            node_type="core_event",
            tag=_("[심층 사건 · 핵심]"),
            title=_("기억의 핵"),
            desc=_("이 차원의 가장 깊은 진실이 잠들어 있는 핵심 기억 구역입니다."),
            reward_hint=_("특징: 메인 스토리 진행 및 특별 보상"),
            is_eroded=False,
        ),
        "boss": AreaNode(
            node_type="boss",
            tag=_("[차원 보스]"),
            title=_("주인 악몽의 심장부"),
            desc=_("차원을 지배하는 주인 악몽을 쓰러뜨려야 다음 심층으로 내려갈 수 있습니다."),
            reward_hint=_("보상: 다음 차원 돌파 및 대량 보상"),
            is_eroded=False,
        ),
    }

    def generate_next_nodes(dim, area, sanity):
        """
        현재 구역 번호(area)에 맞는 다음 구역 선택지 리스트를 반환.
        - 1~5구역: 자유 탐사 (3개 선택지 제시, 이성치 0 이하 시 침식 변질 발생)
        - 6구역: 심층 사건 고정
        - 7구역: 드림링크 중계소(상점/휴식) 고정
        - 8구역: 차원 보스 고정
        """
        if area == 6:
            return [NODE_TEMPLATES["core_event"]]
        elif area == 7:
            return [NODE_TEMPLATES["relay"]]
        elif area == 8:
            return [NODE_TEMPLATES["boss"]]

        # 1~5구역 자유 탐사 풀 구성
        pool = ["battle", "event", "reward"]
        if area >= 2:
            pool.append("elite")
        if area in (3, 4):
            pool.append("relay")

        chosen_keys = random.sample(pool, k=min(3, len(pool)))
        # 사건 비중을 높이기 위해, 만약 사건/자각이 하나도 안 뽑혔다면 하나쯤은 사건으로 보정할 확률 부여
        if "event" not in chosen_keys and random.random() < 0.65:
            chosen_keys[random.randint(0, len(chosen_keys) - 1)] = "event"

        # 이성치 침식(Sanity Erosion) 처리: sanity <= 0일 때 변질
        eroded_map = {
            "battle": "eroded_battle",
            "event": "eroded_event",
            "reward": "eroded_reward",
        }
        if sanity <= 0:
            erosion_chance = min(85, 40 + abs(sanity) // 2)
            eroded_any = False
            new_keys = []
            for k in chosen_keys:
                if k in eroded_map and random.randint(1, 100) <= erosion_chance:
                    new_keys.append(eroded_map[k])
                    eroded_any = True
                else:
                    new_keys.append(k)
            # 이성치가 0 이하인데 침식 가능한 노드가 있다면 최소 1개는 침식되도록 보장
            if not eroded_any:
                erodable_indices = [i for i, k in enumerate(new_keys) if k in eroded_map]
                if erodable_indices:
                    idx = random.choice(erodable_indices)
                    new_keys[idx] = eroded_map[new_keys[idx]]
            chosen_keys = new_keys

        return [NODE_TEMPLATES[k] for k in chosen_keys]

    def build_battle_enemies(dim, mode="normal"):
        """차원 배율(mult)과 전투 종류에 맞는 적 리스트 생성"""
        info = DIMENSION_INFO.get(dim, DIMENSION_INFO[1])
        mult = info["mult"]
        if mode == "normal":
            return [WilloWisp().scale(mult), Teruterubozu().scale(mult)]
        elif mode == "eroded":
            return [WilloWisp().scale(mult * 1.25), Teruterubozu().scale(mult * 1.25)]
        elif mode == "elite":
            return [AbyssWisp().scale(mult), CursedTeru().scale(mult)]
        elif mode == "boss":
            boss = DreamBoss(
                id=info["boss_sprite"],
                name=info["boss_name"],
            ).scale(mult)
            return [boss]
        return [WilloWisp().scale(mult)]

    def play_exploration_bgm(dim, sanity):
        info = DIMENSION_INFO.get(dim, DIMENSION_INFO[1])
        target_bgm = info["bgm_normal"] if sanity > 0 else info["bgm_insane"]
        if renpy.music.get_playing() != target_bgm:
            renpy.music.play(target_bgm, fadeout=1.0, fadein=1.0)


# ==============================================================================
# 탐사 상단 HUD 및 구역 선택 스크린
# ==============================================================================

screen exploration_hud():
    if in_dream_run and not on_battle and currentPlayer is not None:
        python:
            p = currentPlayer
            dim_info = DIMENSION_INFO.get(currentDim, DIMENSION_INFO[1])
            dim_name = dim_info["name"]
            dim_sub = dim_info["subtitle"]
            p_leftbar, p_rightbar = get_bar_colors((p.mp / p.max_mp) * 100 > 20)
            ps_leftbar, ps_rightbar = get_bar_colors(p.sanity > 0)

        # 좌측 상단: 캐릭터 상태창
        frame:
            xanchor 0.0
            yanchor 0.0
            xpos 80
            ypos 60
            xpadding 45
            ypadding 35
            vbox:
                spacing 12
                hbox:
                    spacing 30
                    text "{font=PyeongChang-Bold.ttf}[p.name]{/font}" size 60
                    text "{color=#c184ff}꿈의 파편: [p.dream_shard]{/color}" size 50 yalign 0.5
                    text "공격력 [p.atk] / 방어력 [p.defence]" size 46 color "#cccccc" yalign 0.5
                hbox:
                    spacing 15
                    text _("정신력") size 48 yalign 0.5
                    bar:
                        value AnimatedValue(p.mp, p.max_mp, 0.2)
                        left_bar Solid(p_leftbar)
                        right_bar Solid(p_rightbar)
                        xsize 520
                        ysize 48
                        yalign 0.5
                    text "[p.mp]/[p.max_mp]" size 48 yalign 0.5
                hbox:
                    spacing 15
                    if p.sanity > 0:
                        text _("이성치") size 48 yalign 0.5
                    else:
                        text _("{color=#ff4444}이성치(침식){/color}") size 48 yalign 0.5
                    bar:
                        value AnimatedValue(p.sanity + 100, 200, 0.2)
                        left_bar Solid(ps_leftbar)
                        right_bar Solid(ps_rightbar)
                        xsize 520
                        ysize 48
                        yalign 0.5
                    if p.sanity > 0:
                        text "[p.sanity]/100" size 48 yalign 0.5
                    else:
                        text "{color=#ff4444}[p.sanity]/100{/color}" size 48 yalign 0.5

        # 우측 상단: 현재 차원 및 구역 표시
        frame:
            xanchor 1.0
            yanchor 0.0
            xpos 3760
            ypos 60
            xpadding 50
            ypadding 35
            vbox:
                spacing 8
                text "{font=PyeongChang-Bold.ttf}제[currentDim]차원 : [dim_name]{/font}" size 60 color "#c184ff" xalign 1.0
                text "[dim_sub] — {b}[currentArea] / [MAX_AREA] 구역{/b}" size 48 color "#dddddd" xalign 1.0


screen node_select_ui(nodes):
    modal True
    frame:
        xalign 0.5
        yalign 0.55
        xpadding 80
        ypadding 70
        background Solid("#0d0618dd")
        vbox:
            spacing 45
            xalign 0.5
            vbox:
                spacing 10
                xalign 0.5
                text "{font=PyeongChang-Bold.ttf}다음 구역 선택 ([currentArea] / [MAX_AREA] 구역){/font}" size 80 xalign 0.5 color "#ffffff"
                if currentPlayer.sanity <= 0:
                    text "{color=#ff4444}※ 이성치가 0 이하로 떨어져 일부 구역이 악몽에 침식되었습니다.{/color}" size 50 xalign 0.5
                elif currentArea <= 5:
                    text "나아갈 꿈의 갈래를 선택하세요." size 50 xalign 0.5 color "#bbbbbb"
                else:
                    text "심층의 고정 구역에 도달했습니다." size 50 xalign 0.5 color "#c184ff"

            hbox:
                spacing 60
                xalign 0.5
                for n in nodes:
                    $ card_bg = "#3b0a12ee" if n.is_eroded else "#22103bee"
                    $ card_hover = "#66111fee" if n.is_eroded else "#3d1c6bee"
                    $ tag_color = "#ff5555" if n.is_eroded else "#c184ff"
                    button:
                        xsize 1020
                        ysize 680
                        xpadding 50
                        ypadding 50
                        background Solid(card_bg)
                        hover_background Solid(card_hover)
                        action Return(n.node_type)
                        vbox:
                            spacing 28
                            xalign 0.5
                            yalign 0.5
                            text "{font=PyeongChang-Bold.ttf}[n.tag]{/font}" size 54 color tag_color xalign 0.5
                            text "{font=PyeongChang-Bold.ttf}[n.title]{/font}" size 76 color "#ffffff" xalign 0.5
                            null height 10
                            text "[n.desc]" size 48 color "#dddddd" xalign 0.5 text_align 0.5
                            null height 15
                            text "[n.reward_hint]" size 44 color tag_color xalign 0.5 text_align 0.5


# ==============================================================================
# 1. 현실 베이스캠프: 드림링크 연구실 (로비)
# ==============================================================================

label lab_hub:
    $ in_dream_run = False
    $ on_battle = False
    hide screen exploration_hud
    scene bgplaceholder with dissolve
    play music "Time2Dream.wav" fadeout 1.0 fadein 1.0

    perwin "여기는 드림링크 연구실이야, [currentPlayer.name]."
    perwin "현재 네 자각몽 레벨은 {color=#c184ff}Lv.[playerAccount.level]{/color} (EXP [playerAccount.exp]/100), 보유한 꿈의 결정은 {color=#c184ff}[playerAccount.dream_crystal]개{/color}야."

    label lab_menu:
        menu:
            "드림링크 접속 (꿈세계 탐사 시작)":
                jump start_dream_run
            "페르윈 & 리나트와 대화한다 (연구실 기록)":
                jump lab_talk
            "꿈의 결정으로 드림링크 출력 강화 (영구 보너스 확인)":
                jump lab_upgrade
            "게임 종료":
                stop music fadeout 1.0
                return

label lab_talk:
    if playerAccount.run_count == 0:
        perwin "우리가 만든 자각몽 기계 '드림링크'를 통해 사람들의 꿈이 모이는 곳, '허수의 바다'로 내려가게 될 거야."
        rinat "꿈속에서는 육체가 없으니 {color=#c184ff}정신력(MP){/color}이 곧 생명력이자 스킬을 쓰는 마력이야. 바닥나면 강제로 사출되니까 조심해~"
        perwin "그리고 {color=#cc1100}이성치(Sanity){/color}가 0 이하로 떨어지면 스킬도 뒤틀리고 구역 자체가 침식되기 시작해. 위험하지만… 그 이면에서만 얻을 수 있는 단서도 있을 거야."
    else:
        perwin "벌써 [playerAccount.run_count]번째 다이브네. 심층 사건 진행도는 현재 [playerAccount.story_progress]단계야."
        rinat "각 차원의 6구역에는 '기억의 핵'이 자리 잡고 있어. 깊이 내려갈수록 이 꿈세계의 기원에 가까워질 거야."
    jump lab_menu

label lab_upgrade:
    $ bonus_mp = (playerAccount.level - 1) * 10
    $ bonus_atk = playerAccount.level - 1
    perwin "현재 자각몽 레벨(Lv.[playerAccount.level]) 효과로 탐사 진입 시 최대 정신력이 +[bonus_mp], 공격력이 +[bonus_atk]만큼 보정돼."
    if playerAccount.dream_crystal >= 50:
        menu:
            "꿈의 결정 50개로 자각몽 동조율 즉시 +1 레벨업 (현재 [playerAccount.dream_crystal]개)":
                $ playerAccount.dream_crystal -= 50
                $ playerAccount.level += 1
                perwin "동조율 업그레이드 완료! 이제 Lv.[playerAccount.level](이)야."
            "돌아간다":
                pass
    else:
        perwin "추가 동조율 강화를 하려면 꿈의 결정이 최소 50개 필요해. 탐사를 다녀오면 깊이에 비례해서 얻을 수 있어."
    jump lab_menu


# ==============================================================================
# 2. 탐사 시작 및 차원 진입 루프
# ==============================================================================

label start_dream_run:
    python:
        # 새 탐사(Run) 초기화
        saved_name = currentPlayer.name
        currentPlayer = Tester(name=saved_name)
        # 자각몽 레벨 영구 보너스 반영
        currentPlayer.max_mp += (playerAccount.level - 1) * 10
        currentPlayer.mp = currentPlayer.max_mp
        currentPlayer.atk += (playerAccount.level - 1)
        currentDim = 1
        currentArea = 1
        visitedEvents = []
        in_dream_run = True
        run_cleared = False

    show screen exploration_hud
    perwin "드림링크 접속 개시. 목표는 총 3개 차원을 돌파해 가장 깊은 허수의 바다에 도달하는 거야."
    jump enter_dimension


label enter_dimension:
    $ dim_info = DIMENSION_INFO[currentDim]
    $ dim_name = dim_info["name"]
    $ dim_sub = dim_info["subtitle"]
    $ play_exploration_bgm(currentDim, currentPlayer.sanity)
    scene bgplaceholder with fade

    "— {font=PyeongChang-Bold.ttf}제[currentDim]차원 : [dim_name]{/font} ([dim_sub]) —"

    if currentDim == 1:
        rinat "제1차원 표층몽에 진입했어! 본격적으로 1구역 탐사를 시작하기 전에 초기 동기화 지원을 하나 골라봐."
        menu:
            "[[안정 동기화] 최대 정신력 +30 및 정신력 회복":
                $ currentPlayer.max_mp += 30
                $ currentPlayer.mp = currentPlayer.max_mp
                "정신의 방벽이 두터워졌습니다. (최대 정신력 +30)"
            "[[공격 동기화] 공격력 +4, 치명타 확률 +10%%":
                $ currentPlayer.atk += 4
                $ currentPlayer.crit_chance += 10
                "의식이 날카롭게 벼려집니다. (공격력 +4, 치명타 확률 +10%%)"
            "[[물질 동기화] 꿈의 파편 +150 획득":
                $ currentPlayer.dream_shard += 150
                "응결된 꿈의 파편을 150개 확보했습니다."
            "{color=#cc1100}[[금기 동기화] 이성치 -110 (즉시 광기/침식 진입), 공격력 +7{/color}":
                $ currentPlayer.take_sanity(110)
                $ currentPlayer.atk += 7
                $ play_exploration_bgm(currentDim, currentPlayer.sanity)
                "드림링크의 안전 리미터를 해제했습니다! 이성이 급감하는 대신 강력한 힘이 솟구칩니다."
    else:
        perwin "보스를 쓰러뜨리고 더 깊은 층, {color=#c184ff}제[currentDim]차원 [dim_name]{/color}(으)로 하강했어."
        rinat "심층 하강 보너스야! 다음 구역으로 가기 전에 하나를 선택해."
        menu:
            "정신력을 50%% 회복하고 최대 정신력 +20":
                $ currentPlayer.max_mp += 20
                $ currentPlayer.heal(currentPlayer.max_mp // 2)
                "깊은 숨을 내쉬며 정신력을 추슬렀습니다."
            "공격력 +5 및 방어력 +5 상승":
                $ currentPlayer.atk += 5
                $ currentPlayer.defence += 5
                "더 깊은 악몽에 맞서기 위해 의식을 강화했습니다."
            "이성치를 +40 회복하고 꿈의 파편 +100 획득":
                $ currentPlayer.recover_sanity(40)
                $ currentPlayer.dream_shard += 100
                "흔들리던 이성을 다잡고 파편을 수거했습니다."

    jump exploration_loop


label exploration_loop:
    while in_dream_run:
        $ play_exploration_bgm(currentDim, currentPlayer.sanity)
        $ next_nodes = generate_next_nodes(currentDim, currentArea, currentPlayer.sanity)
        call screen node_select_ui(next_nodes)
        $ chosen_node_type = _return

        if chosen_node_type == "battle":
            call node_battle("normal")
        elif chosen_node_type == "eroded_battle":
            call node_battle("eroded")
        elif chosen_node_type == "elite":
            call node_battle("elite")
        elif chosen_node_type == "event":
            call node_event("normal")
        elif chosen_node_type == "eroded_event":
            call node_event("eroded")
        elif chosen_node_type == "reward":
            call node_reward(is_eroded=False)
        elif chosen_node_type == "eroded_reward":
            call node_reward(is_eroded=True)
        elif chosen_node_type == "relay":
            call node_relay
        elif chosen_node_type == "core_event":
            call node_event("core")
        elif chosen_node_type == "boss":
            call node_boss

        # 구역 진행 도중 정신력(MP)이 0 이하가 되었다면 탐사 실패 처리
        if currentPlayer.mp <= 0:
            $ in_dream_run = False
            $ run_cleared = False
            jump run_settlement

        # 보스 구역(8구역)까지 클리어했다면 다음 차원으로 이동하거나 최종 클리어
        if currentArea >= MAX_AREA:
            if currentDim < MAX_DIM:
                $ currentDim += 1
                $ currentArea = 1
                jump enter_dimension
            else:
                $ in_dream_run = False
                $ run_cleared = True
                jump run_settlement
        else:
            $ currentArea += 1

    jump run_settlement


# ==============================================================================
# 3. 각 구역(Node) 상세 동작
# ==============================================================================

label node_battle(mode="normal"):
    if mode == "normal":
        "전방에서 배회하는 악몽들이 모습을 드러냅니다!"
        $ enemies = build_battle_enemies(currentDim, "normal")
        call battle(enemies, phase_count=2)
    elif mode == "eroded":
        "{color=#cc1100}[[광란의 전투]{/color} 침식된 공간에서 폭주하는 악몽 무리가 몰려옵니다!"
        $ enemies = build_battle_enemies(currentDim, "eroded")
        call battle(enemies, phase_count=3)
    elif mode == "elite":
        "{color=#c184ff}[[정예 조우]{/color} 짙은 악몽의 기운이 공간을 짓누릅니다!"
        $ enemies = build_battle_enemies(currentDim, "elite")
        call battle(enemies, phase_count=1)

    $ won = _return
    if not won:
        return

    $ play_exploration_bgm(currentDim, currentPlayer.sanity)

    python:
        if mode == "normal":
            shard_gain = 40 + currentDim * 15
        elif mode == "eroded":
            shard_gain = 75 + currentDim * 25
        else:
            shard_gain = 90 + currentDim * 30
        currentPlayer.dream_shard += shard_gain

    "전투에서 승리하여 {color=#c184ff}꿈의 파편 [shard_gain]개{/color}를 획득했습니다!"
    call post_battle_blessing(mode)
    return


label post_battle_blessing(mode="normal"):
    # 추후 물결(축복) 시스템이 들어갈 자리 (현재는 프로토타입 공명 보너스 선택)
    python:
        stat_scale = 2 if mode in ("eroded", "elite", "boss") else 1
        b_atk = 2 * stat_scale
        b_heal1 = 15 * stat_scale
        b_def = 3 * stat_scale
        b_maxmp = 10 * stat_scale
        b_san = 15 * stat_scale
        b_cdmg = round(0.15 * stat_scale, 2)
        b_heal2 = 25 * stat_scale
    menu:
        "전투 후 꿈의 물결이 공명합니다. 흡수할 힘을 선택하세요."
        "[[파괴의 물결] 공격력 +[b_atk] 및 정신력 [b_heal1] 회복":
            $ currentPlayer.atk += b_atk
            $ currentPlayer.heal(b_heal1)
        "[[수호의 물결] 방어력 +[b_def] 및 최대 정신력 +[b_maxmp]":
            $ currentPlayer.defence += b_def
            $ currentPlayer.max_mp += b_maxmp
            $ currentPlayer.heal(b_maxmp)
        "[[광기의 물결] 이성치 -[b_san], 치명타 피해 +[b_cdmg]배 및 정신력 [b_heal2] 회복":
            $ currentPlayer.take_sanity(b_san)
            $ currentPlayer.crit_damage = round(currentPlayer.crit_damage + b_cdmg, 2)
            $ currentPlayer.heal(b_heal2)
    return


label node_reward(is_eroded=False):
    if not is_eroded:
        "— {color=#c184ff}[[자각 구역] 무의식 공명 지점{/color} —"
        "고요한 꿈의 틈새를 발견했습니다. 이곳에서는 스스로의 자각몽을 조율하여 원하는 보상을 이끌어낼 수 있습니다."
        menu:
            "[[기억 채굴] 꿈의 파편 +100 획득 및 정신력 20 회복":
                $ currentPlayer.dream_shard += 100
                $ currentPlayer.heal(20)
                "흩어진 꿈의 파편을 모으고 숨을 돌렸습니다."
            "[[자각 강화] 공격력 +3, 방어력 +3 상승":
                $ currentPlayer.atk += 3
                $ currentPlayer.defence += 3
                "꿈속의 법칙을 재정의하여 신체를 강화했습니다."
            "[[정신 정화] 정신력 40 회복 및 이성치 +25 회복":
                $ currentPlayer.heal(40)
                $ currentPlayer.recover_sanity(25)
                "맑은 파동이 머릿속의 안개를 걷어냅니다."
    else:
        "— {color=#cc1100}[[금기된 자각] 심연의 등가교환{/color} —"
        "일그러진 제단 위에서 검은 결정들이 속삭입니다. 대가를 바치면 그 이상의 힘을 손에 넣을 수 있습니다."
        menu:
            "{color=#cc1100}[[피의 서약] 현재 정신력 30%% 소모 → 공격력 +7 및 꿈의 파편 +120{/color}":
                $ currentPlayer.harm(int(currentPlayer.mp * 0.3))
                $ currentPlayer.atk += 7
                $ currentPlayer.dream_shard += 120
                "고통과 함께 압도적인 파괴력이 혈관을 타고 흐릅니다!"
            "{color=#cc1100}[[광기 수용] 이성치 -30 → 최대 정신력 +40 및 즉시 정신력 50 회복{/color}":
                $ currentPlayer.take_sanity(30)
                $ currentPlayer.max_mp += 40
                $ currentPlayer.heal(50)
                "이성을 내려놓자 오히려 정신의 그릇이 비정상적으로 확장됩니다!"
            "[[거부] 제단을 무시하고 그냥 지나간다 (이성치 +10)":
                $ currentPlayer.recover_sanity(10)
                "유혹을 뿌리치고 제단을 뒤로했습니다."
    return


label node_relay:
    $ terminal_used = False
    "— {color=#c184ff}[[중계소] 드림링크 안전지대{/color} —"
    perwin "치직— 아, 연결됐다! [currentPlayer.name], 상태는 괜찮아?"
    rinat "보스 구역에 들어가기 전에 단말기에서 정신력을 정비하거나, 모은 꿈의 파편으로 거래를 할 수 있어~"

    label relay_menu:
        menu:
            "페르윈의 터미널: 정신력 & 이성치 정비 (1회)" if not terminal_used:
                jump relay_terminal
            "리나트의 상점: 꿈의 파편으로 강화 구매 (보유: [currentPlayer.dream_shard]개)":
                jump relay_shop
            "정비를 마치고 다음 구역으로 출발한다":
                perwin "건투를 빌게. 신호가 끊기지 않게 주의해!"
                return

label relay_terminal:
    menu:
        "페르윈의 원격 드림링크 조정 기능을 선택하세요. (중계소 방문당 1회 이용 가능)"
        "[[뇌파 안정화] 정신력 50%% 회복 및 이성치 +25 회복":
            $ terminal_used = True
            $ currentPlayer.heal(currentPlayer.max_mp // 2)
            $ currentPlayer.recover_sanity(25)
            $ play_exploration_bgm(currentDim, currentPlayer.sanity)
            perwin "뇌파 출력 안정화 완료. 한결 버티기 수월할 거야."
        "[[드림링크 과부하] 이성치 -35 삭감, 정신력 40%% 회복 및 공격력 +3":
            $ terminal_used = True
            $ currentPlayer.take_sanity(35)
            $ currentPlayer.heal(int(currentPlayer.max_mp * 0.4))
            $ currentPlayer.atk += 3
            $ play_exploration_bgm(currentDim, currentPlayer.sanity)
            perwin "출력 리미터를 더 풀었어. 정신줄 단단히 잡아!"
        "돌아간다":
            pass
    jump relay_menu

label relay_shop:
    menu:
        "리나트: '꿈의 파편만 충분하다면 뭐든 조율해 줄게!' (보유 파편: [currentPlayer.dream_shard]개)"
        "[[파편 80개] 정신력 완전 회복" if currentPlayer.dream_shard >= 80:
            $ currentPlayer.dream_shard -= 80
            $ currentPlayer.mp = currentPlayer.max_mp
            rinat "정신력 100%% 충전 완료~!"
        "[[파편 100개] 무의식 증폭기 (공격력 +4)" if currentPlayer.dream_shard >= 100:
            $ currentPlayer.dream_shard -= 100
            $ currentPlayer.atk += 4
            rinat "공격력을 높여뒀어. 악몽들을 시원하게 날려버려!"
        "[[파편 100개] 허상 방벽 코어 (방어력 +5, 최대 정신력 +20)" if currentPlayer.dream_shard >= 100:
            $ currentPlayer.dream_shard -= 100
            $ currentPlayer.defence += 5
            $ currentPlayer.max_mp += 20
            $ currentPlayer.heal(20)
            rinat "방어 코어 장착 완료! 이제 훨씬 덜 아플 거야."
        "[[파편 120개] 금단의 아르카나 프로토타입 (치명타 확률 +15%%, 치명타 피해 +0.3배)" if currentPlayer.dream_shard >= 120:
            $ currentPlayer.dream_shard -= 120
            $ currentPlayer.crit_chance += 15
            $ currentPlayer.crit_damage = round(currentPlayer.crit_damage + 0.3, 2)
            rinat "후후, 꽤 희귀한 기물을 골랐네?"
        "상점을 나간다":
            jump relay_menu
    jump relay_shop


label node_boss:
    $ dim_info = DIMENSION_INFO[currentDim]
    $ boss_name = dim_info["boss_name"]
    "— {color=#ff4444}[[제[currentDim]차원 보스 구역]{/color} —"
    perwin "강대한 파형이 감지돼! 이 차원의 주인 악몽, {color=#ff4444}[boss_name]{/color}(이)야!"
    $ boss_enemies = build_battle_enemies(currentDim, "boss")
    call battle(boss_enemies, phase_count=1)
    $ won = _return
    if not won:
        return

    $ play_exploration_bgm(currentDim, currentPlayer.sanity)
    $ boss_shard = 150 * currentDim
    $ currentPlayer.dream_shard += boss_shard
    "주인 악몽을 물리쳤습니다! {color=#c184ff}꿈의 파편 [boss_shard]개{/color}를 획득했습니다!"
    call post_battle_blessing("boss")
    return


# ==============================================================================
# 4. 탐사 종료 및 정산
# ==============================================================================

label run_settlement:
    $ in_dream_run = False
    $ on_battle = False
    hide screen exploration_hud
    scene bgplaceholder with fade
    play music "Time2Dream.wav" fadeout 1.0 fadein 1.0

    python:
        playerAccount.run_count += 1
        old_level = playerAccount.level
        gained_exp, gained_crystal = playerAccount.getEXP(currentDim, currentArea)
        if run_cleared:
            # 최종 클리어 보너스
            playerAccount.dream_crystal += 100
            gained_crystal += 100

    if run_cleared:
        "축하합니다! 제3차원 허수의 바다 끝까지 주파하여 탐사에 성공했습니다!"
        perwin "믿을 수가 없군… 정말로 제3차원의 주인 악몽까지 뚫어냈어!"
    else:
        "정신력이 고갈되어 드림링크 안전장치가 작동했습니다. 현실의 연구실로 강제 사출됩니다..."
        perwin "정신이 무사해서 다행이야. 제[currentDim]차원 [currentArea]구역까지 데이터를 회수했어."

    "— {font=PyeongChang-Bold.ttf}[[탐사 정산 결과]{/font} —\n도달 깊이: 제[currentDim]차원 [currentArea]구역\n획득 경험치: +{color=#c184ff}[gained_exp] EXP{/color} (자각몽 레벨 Lv.[old_level] → {color=#c184ff}Lv.[playerAccount.level]{/color})\n획득 꿈의 결정: +{color=#c184ff}[gained_crystal]개{/color} (총 [playerAccount.dream_crystal]개)"

    jump lab_hub