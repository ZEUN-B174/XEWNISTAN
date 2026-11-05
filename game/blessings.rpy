# 물결(축복, Wave) 및 아르카나(기물, Arcana) 시스템
# - 5대 물결 갈래: 파열(자해/광기), 청명(이성/회복), 격류(치명/연격), 침잠(방어/반격), 잠식(침식/디버프)
# - 물결 등급(★1 ~ ★3) 및 강화(upgraded) 지원, 동일 갈래 3개 보유 시 [갈래 공명] 시너지 발동
# - 아르카나: 회중시계, 몽마의 립스틱, 깨진 거울 등 꿈속의 기묘한 물건(유물) 형태

init 2 python:
    import copy
    import random
    from dataclasses import dataclass

    # ==========================================================================
    # 1. 물결(Wave) 5대 갈래 및 3셋 공명 시너지 정의
    # ==========================================================================
    WAVE_PATHS = {
        "rupture": {
            "name": _("파열"),
            "sub": _("자해 · 역전"),
            "color": "#ff4d4d",
            "synergy_name": _("파열 공명 : 피의 갈망"),
            "synergy_desc": _("파열 물결 3개 보유 시 활성화 — 잃은 정신력 10%당 최종 공격력 +5% 증가, [자해] 시 정신력 소모량 20% 경감"),
        },
        "clarity": {
            "name": _("청명"),
            "sub": _("이성 · 정화"),
            "color": "#5ce1e6",
            "synergy_name": _("청명 공명 : 맑은 거울"),
            "synergy_desc": _("청명 물결 3개 보유 시 활성화 — 이성치가 0보다 클 때 모든 받는 피해 15% 감소 및 매 턴 정신력 6 회복"),
        },
        "torrent": {
            "name": _("격류"),
            "sub": _("치명 · 연격"),
            "color": "#ffbb33",
            "synergy_name": _("격류 공명 : 몰아치는 해일"),
            "synergy_desc": _("격류 물결 3개 보유 시 활성화 — 치명타 확률 +15%, 치명타 피해 +30% 증가"),
        },
        "submerge": {
            "name": _("침잠"),
            "sub": _("방어 · 반격"),
            "color": "#9966ff",
            "synergy_name": _("침잠 공명 : 심해의 요새"),
            "synergy_desc": _("침잠 물결 3개 보유 시 활성화 — 방어력 +25% 증가, 피격 시 자신의 방어력 80%만큼 적에게 반격 피해"),
        },
        "erosion": {
            "name": _("잠식"),
            "sub": _("침식 · 저주"),
            "color": "#e879f9",
            "synergy_name": _("잠식 공명 : 심연의 포자"),
            "synergy_desc": _("잠식 물결 3개 보유 시 활성화 — 이성치가 0 이하일 때 공격력 +25% 증가, 디버프 걸린 적에게 가하는 피해 +20%"),
        },
    }

    @dataclass
    class Wave:
        id: str
        name: str
        path: str           # "rupture", "clarity", "torrent", "submerge", "erosion"
        rarity: int         # 1, 2, 3 (★1 ~ ★3)
        desc_base: str      # 기본 설명
        desc_up: str        # 강화(+) 후 설명
        upgraded: bool = False

        @property
        def display_name(self):
            return f"{self.name}+" if self.upgraded else self.name

        @property
        def desc(self):
            return self.desc_up if self.upgraded else self.desc_base

        @property
        def path_info(self):
            return WAVE_PATHS.get(self.path, WAVE_PATHS["clarity"])

        @property
        def stars_str(self):
            return "★" * self.rarity

    # ==========================================================================
    # 2. 물결(Wave) 도감 레지스트리 (갈래별 ★1 ~ ★3)
    # ==========================================================================
    WAVE_REGISTRY = [
        # --- [파열 (Rupture) : 자해 · 역전] ---
        Wave(
            id="rup_1_adrenaline",
            name=_("붉은 잔물결"),
            path="rupture",
            rarity=1,
            desc_base=_("[자해] 발동 시 2턴간 공격력 +25% 버프를 획득한다."),
            desc_up=_("[자해] 발동 시 2턴간 공격력 +40% 버프를 획득한다."),
        ),
        Wave(
            id="rup_1_backflow",
            name=_("고통의 역류"),
            path="rupture",
            rarity=1,
            desc_base=_("잃은 정신력 10%마다 공격력이 +4% 증가한다."),
            desc_up=_("잃은 정신력 10%마다 공격력이 +7% 증가한다."),
        ),
        Wave(
            id="rup_2_crimson_echo",
            name=_("피투성이 메아리"),
            path="rupture",
            rarity=2,
            desc_base=_("[자해] 발동 시 현재 적에게 공격력 120%의 추가 피해를 가한다."),
            desc_up=_("[자해] 발동 시 현재 적에게 공격력 180%의 추가 피해를 가한다."),
        ),
        Wave(
            id="rup_3_guillotine",
            name=_("불사조의 단두대"),
            path="rupture",
            rarity=3,
            desc_base=_("전투당 1회, [자살] 또는 정신력이 0이 될 때 죽지 않고 정신력을 50% 회복하며 적에게 공격력 450%의 피해를 가한다."),
            desc_up=_("전투당 1회, [자살] 또는 정신력이 0이 될 때 죽지 않고 정신력을 80% 회복하며 적에게 공격력 650%의 피해를 가한다."),
        ),

        # --- [청명 (Clarity) : 이성 · 정화] ---
        Wave(
            id="cla_1_calm_surface",
            name=_("고요한 수면"),
            path="clarity",
            rarity=1,
            desc_base=_("이성치가 0보다 클 때 공격력 +15%, 방어력 +15% 증가한다."),
            desc_up=_("이성치가 0보다 클 때 공격력 +25%, 방어력 +25% 증가한다."),
        ),
        Wave(
            id="cla_1_deep_breath",
            name=_("정화의 숨결"),
            path="clarity",
            rarity=1,
            desc_base=_("매 턴 종료 시 최대 정신력의 6%만큼 정신력을 회복한다."),
            desc_up=_("매 턴 종료 시 최대 정신력의 10%만큼 정신력을 회복하고 이성치를 +2 회복한다."),
        ),
        Wave(
            id="cla_2_lucid_flow",
            name=_("자각의 흐름"),
            path="clarity",
            rarity=2,
            desc_base=_("모든 스킬의 정신력(MP) 소모량이 30% 감소하고, 전투 승리 시 정신력을 15 회복한다."),
            desc_up=_("모든 스킬의 정신력(MP) 소모량이 45% 감소하고, 전투 승리 시 정신력을 25 회복한다."),
        ),
        Wave(
            id="cla_3_mirror_light",
            name=_("무결한 거울빛"),
            path="clarity",
            rarity=3,
            desc_base=_("정신력을 회복할 때마다 회복량의 90%만큼 적에게 피해를 가하고 이성치를 +4 회복한다."),
            desc_up=_("정신력을 회복할 때마다 회복량의 140%만큼 적에게 피해를 가하고 이성치를 +7 회복한다."),
        ),

        # --- [격류 (Torrent) : 치명 · 연격] ---
        Wave(
            id="tor_1_sharp_wave",
            name=_("예리한 파도"),
            path="torrent",
            rarity=1,
            desc_base=_("치명타 확률 +15%, 치명타 피해 +20% 증가한다."),
            desc_up=_("치명타 확률 +25%, 치명타 피해 +35% 증가한다."),
        ),
        Wave(
            id="tor_1_splash",
            name=_("몰아치는 물보라"),
            path="torrent",
            rarity=1,
            desc_base=_("공격 적중 시 40% 확률로 공격력 50%의 추가 피해를 가한다."),
            desc_up=_("공격 적중 시 60% 확률로 공격력 75%의 추가 피해를 가한다."),
        ),
        Wave(
            id="tor_2_chain_foam",
            name=_("연쇄 포말"),
            path="torrent",
            rarity=2,
            desc_base=_("적을 처치할 때마다 정신력을 20 회복하고 2턴간 공격력 +30% 버프를 얻는다."),
            desc_up=_("적을 처치할 때마다 정신력을 35 회복하고 2턴간 공격력 +50% 버프를 얻는다."),
        ),
        Wave(
            id="tor_3_abyss_storm",
            name=_("심해의 폭풍"),
            path="torrent",
            rarity=3,
            desc_base=_("모든 공격의 타격 피해가 30% 증폭되고, 공격 적중 시마다 치명타 피해가 이번 전투 동안 +5%(최대 +50%) 누적된다."),
            desc_up=_("모든 공격의 타격 피해가 45% 증폭되고, 공격 적중 시마다 치명타 피해가 이번 전투 동안 +8%(최대 +80%) 누적된다."),
        ),

        # --- [침잠 (Submerge) : 방어 · 반격] ---
        Wave(
            id="sub_1_abyss_armor",
            name=_("해저의 중갑"),
            path="submerge",
            rarity=1,
            desc_base=_("방어력 +30% 및 최대 정신력 +25 증가한다."),
            desc_up=_("방어력 +50% 및 최대 정신력 +45 증가한다."),
        ),
        Wave(
            id="sub_1_thorn_coral",
            name=_("가시 산호초"),
            path="submerge",
            rarity=1,
            desc_base=_("적에게 피격당할 때마다 자신의 방어력 120%만큼 적에게 반격 피해를 가한다."),
            desc_up=_("적에게 피격당할 때마다 자신의 방어력 190%만큼 적에게 반격 피해를 가한다."),
        ),
        Wave(
            id="sub_2_trench_ward",
            name=_("부동의 해저"),
            path="submerge",
            rarity=2,
            desc_base=_("받는 정신력 피해가 20% 감소하고, 적에게 받는 이성치 피해가 35% 감소한다."),
            desc_up=_("받는 정신력 피해가 32% 감소하고, 적에게 받는 이성치 피해가 50% 감소한다."),
        ),
        Wave(
            id="sub_3_titan_trench",
            name=_("거대한 해구"),
            path="submerge",
            rarity=3,
            desc_base=_("자신의 방어력의 50%만큼 공격력이 추가로 증가하고, 전투 시작 시 최대 정신력의 15%를 회복한다."),
            desc_up=_("자신의 방어력의 80%만큼 공격력이 추가로 증가하고, 전투 시작 시 최대 정신력의 25%를 회복한다."),
        ),

        # --- [잠식 (Erosion) : 침식 · 저주] ---
        Wave(
            id="ero_1_curse_bubble",
            name=_("불길한 거품"),
            path="erosion",
            rarity=1,
            desc_base=_("공격 적중 시 적에게 2턴간 [침식](방어력 -25%, 매 턴 정신력 -8 피해)을 부여한다."),
            desc_up=_("공격 적중 시 적에게 3턴간 [침식+](방어력 -35%, 매 턴 정신력 -14 피해)을 부여한다."),
        ),
        Wave(
            id="ero_1_mad_whisper",
            name=_("광기의 속삭임"),
            path="erosion",
            rarity=1,
            desc_base=_("이성치가 0 이하일 때, 잃은 이성치(절댓값) 10당 공격력이 +6% 증가한다."),
            desc_up=_("이성치가 0 이하일 때, 잃은 이성치(절댓값) 10당 공격력이 +10% 증가한다."),
        ),
        Wave(
            id="ero_2_fear_spread",
            name=_("공포 전염"),
            path="erosion",
            rarity=2,
            desc_base=_("디버프가 걸린 적을 공격할 때 피해량이 +25% 증가하고 정신력을 8 흡수한다."),
            desc_up=_("디버프가 걸린 적을 공격할 때 피해량이 +40% 증가하고 정신력을 14 흡수한다."),
        ),
        Wave(
            id="ero_3_void_vortex",
            name=_("허수의 소용돌이"),
            path="erosion",
            rarity=3,
            desc_base=_("혼돈 스킬 사용 시 또는 이성치가 감소할 때마다 적에게 공격력 140% 피해를 가하고 2턴간 받는 피해 +25% 디버프를 부여한다."),
            desc_up=_("혼돈 스킬 사용 시 또는 이성치가 감소할 때마다 적에게 공격력 210% 피해를 가하고 2턴간 받는 피해 +40% 디버프를 부여한다."),
        ),
    ]

    # ==========================================================================
    # 3. 아르카나(Arcana : 꿈의 기물/유물) 정의 및 레지스트리
    # ==========================================================================
    @dataclass
    class Arcana:
        id: str
        name: str
        subtitle: str       # 짧은 플레이버 텍스트/부제
        desc: str           # 기물 효과 설명
        is_cursed: bool = False  # 금기/침식 기물 여부

    ARCANA_REGISTRY = [
        Arcana(
            id="broken_watch",
            name=_("멈춰버린 회중시계"),
            subtitle=_("바늘이 3시 33분에 고정된 낡은 은시계"),
            desc=_("전투 시작 시 2턴간 공격력 +35% 및 치명타 확률 +25% 버프를 얻는다. 사건 구역에서 시간 관련 특수 선택지가 해금된다."),
        ),
        Arcana(
            id="succubus_lipstick",
            name=_("몽마의 루주"),
            subtitle=_("리나트가 실수로 꿈속에 떨어뜨린 화장품"),
            desc=_("중계소(리나트의 상점)의 모든 가격 25% 할인. 전투 승리 시마다 정신력을 10 회복한다."),
        ),
        Arcana(
            id="black_umbrella",
            name=_("검은 우산"),
            subtitle=_("비를 막아주지 못하는 축축한 우산"),
            desc=_("방어력 +6 증가. 구역을 이동할 때마다 정신력을 12 회복하고 이성치를 +5 회복한다."),
        ),
        Arcana(
            id="bloodied_scalpel",
            name=_("녹슨 해부용 메스"),
            subtitle=_("누군가의 악몽에서 건져 올린 차가운 금속"),
            desc=_("치명타 피해 +35% 증가. [자해] 발동 시마다 꿈의 파편을 25개 획득한다."),
            is_cursed=True,
        ),
        Arcana(
            id="white_noise_tape",
            name=_("백색소음 카세트테이프"),
            subtitle=_("라벨에 '절대 재생하지 말 것'이라 적힌 테이프"),
            desc=_("이성치가 0 이하일 때 매 턴 광기(혼돈 스킬) 발동 확률이 +35%p 증가하고, 혼돈 스킬의 피해량이 +30% 증가한다."),
            is_cursed=True,
        ),
        Arcana(
            id="golden_dreamcatcher",
            name=_("황금빛 드림캐처"),
            subtitle=_("악몽을 걸러내어 결정으로 바꾸는 장식"),
            desc=_("전투 승리 시 획득하는 꿈의 파편이 +40% 증가하고, 획득 즉시 꿈의 파편 +80개를 얻는다."),
        ),
        Arcana(
            id="emergency_sedative",
            name=_("비상용 신경 안정제"),
            subtitle=_("드림링크 실험실의 응급 키트"),
            desc=_("전투당 1회, 정신력이 30% 이하로 떨어지면 즉시 최대 정신력의 40%를 회복하고 2턴간 방어력 +40% 버프를 얻는다."),
        ),
        Arcana(
            id="perwin_dongle",
            name=_("페르윈의 해킹 동글"),
            subtitle=_("꿈세계의 백도어를 여는 개조 USB"),
            desc=_("물결 선택 시 [무료 재굴림 1회] 제공. 전투 시작 시 모든 적에게 3턴간 방어력 -20% 디버프를 부여한다."),
        ),
        Arcana(
            id="eternal_ice",
            name=_("녹지 않는 만년빙"),
            subtitle=_("가장 깊은 무의식에서 얼어붙은 기억 조각"),
            desc=_("최대 정신력 +35 증가. 적에게 피격 시 적에게 2턴간 공격력 -20% 디버프를 부여한다."),
        ),
        Arcana(
            id="schrodinger_dice",
            name=_("슈뢰딩거의 주사위"),
            subtitle=_("던지기 전까진 눈금을 알 수 없는 육면체"),
            desc=_("매 턴 시작 시 공격력 +25%, 방어력 +30%, 치명타 확률 +25% 중 무작위 버프 1개를 1턴간 획득한다."),
        ),
    ]

    # ==========================================================================
    # 4. 물결 & 아르카나 추첨 헬퍼 함수
    # ==========================================================================
    def roll_wave_choices(player, count=3, mode="normal", preferred_path=None):
        """
        플레이어가 아직 보유하지 않은 물결 중에서 count개를 추첨하여 반환.
        mode: "normal" | "eroded" | "elite" | "boss"
        """
        owned_ids = {w.id for w in player.waves}
        unowned = [w for w in WAVE_REGISTRY if w.id not in owned_ids]
        if not unowned:
            return []

        # 등급 가중치 설정
        if mode == "boss":
            weights_by_rarity = {1: 10, 2: 35, 3: 55}
        elif mode in ("elite", "eroded"):
            weights_by_rarity = {1: 25, 2: 50, 3: 25}
        else:
            weights_by_rarity = {1: 60, 2: 32, 3: 8}

        picked = []
        pool = list(unowned)
        for _ in range(min(count, len(pool))):
            weights = []
            for w in pool:
                wt = weights_by_rarity.get(w.rarity, 20)
                if preferred_path and w.path == preferred_path:
                    wt *= 3
                # 이성치가 0 이하일 때는 파열/잠식 갈래 등장 확률 보너스
                if player.sanity <= 0 and w.path in ("rupture", "erosion"):
                    wt = int(wt * 1.5)
                weights.append(wt)
            chosen = random.choices(pool, weights=weights, k=1)[0]
            picked.append(copy.deepcopy(chosen))
            pool.remove(chosen)
        return picked

    def roll_arcana_choices(player, count=3, include_cursed=True):
        owned_ids = {a.id for a in player.arcanas}
        pool = [
            a for a in ARCANA_REGISTRY
            if a.id not in owned_ids and (include_cursed or not a.is_cursed)
        ]
        if not pool:
            return []
        picked = random.sample(pool, k=min(count, len(pool)))
        return [copy.deepcopy(a) for a in picked]


# ==============================================================================
# 5. 물결 선택 / 아르카나 선택 / 물결 강화 UI 스크린
# ==============================================================================

screen wave_select_ui(wave_list, title_text="공명할 물결(축복)을 선택하세요", allow_reroll=True):
    modal True
    zorder 100
    default rerolls_left = (1 if currentPlayer.has_arcana("perwin_dongle") else 0)
    default current_choices = wave_list

    add Solid("#05020acc")

    frame:
        xalign 0.5
        yalign 0.5
        xpadding 80
        ypadding 70
        background Solid("#110722f2")
        vbox:
            spacing 40
            xalign 0.5

            vbox:
                spacing 10
                xalign 0.5
                text "{font=PyeongChang-Bold.ttf}[title_text]{/font}" size 76 color "#ffffff" xalign 0.5
                hbox:
                    spacing 35
                    xalign 0.5
                    for path_key, pinfo in WAVE_PATHS.items():
                        $ cnt = currentPlayer.count_wave_path(path_key)
                        $ pcol = pinfo["color"]
                        $ pname = pinfo["name"]
                        if cnt >= 3:
                            text "{font=PyeongChang-Bold.ttf}{color=[pcol]}[[[pname] [cnt]/3 공명 활성!]{/color}{/font}" size 42
                        else:
                            text "{color=[pcol]}[[[pname] [cnt]/3]{/color}" size 42

            hbox:
                spacing 55
                xalign 0.5
                for w in current_choices:
                    $ pinfo = w.path_info
                    $ pcol = pinfo["color"]
                    $ pname = pinfo["name"]
                    $ psub = pinfo["sub"]
                    $ p_cnt = currentPlayer.count_wave_path(w.path)
                    $ card_bg = "#2a1246ee" if w.rarity == 3 else ("#1f1038ee" if w.rarity == 2 else "#160b28ee")
                    $ card_hover = "#441d70ee"
                    button:
                        xsize 1020
                        ysize 740
                        xpadding 50
                        ypadding 50
                        background Solid(card_bg)
                        hover_background Solid(card_hover)
                        action Return(w)
                        vbox:
                            spacing 22
                            xalign 0.5
                            yalign 0.5
                            hbox:
                                spacing 18
                                xalign 0.5
                                text "{font=PyeongChang-Bold.ttf}{color=[pcol]}[[[pname] · [psub]]{/color}{/font}" size 46
                                text "{font=PyeongChang-Bold.ttf}{color=#ffd700}[w.stars_str]{/color}{/font}" size 46
                            text "{font=PyeongChang-Bold.ttf}[w.display_name]{/font}" size 70 color "#ffffff" xalign 0.5 text_align 0.5
                            null height 8
                            text "[w.desc]" size 46 color "#e2e2e2" xalign 0.5 text_align 0.5
                            null height 12
                            if p_cnt == 2:
                                text "{color=[pcol]}★ 선택 시 [[[pname]] 3개 공명 시너지 발동!{/color}" size 40 xalign 0.5
                            else:
                                text "{color=#aaaaaa}현재 보유 [[[pname]] 물결: [p_cnt]개{/color}" size 40 xalign 0.5

            if allow_reroll:
                hbox:
                    spacing 40
                    xalign 0.5
                    if rerolls_left > 0:
                        textbutton "{font=PyeongChang-Bold.ttf}{color=#5ce1e6}[[해킹 동글] 무료 재굴림 ([rerolls_left]회 남음){/color}{/font}":
                            text_size 48
                            action [
                                SetScreenVariable("rerolls_left", rerolls_left - 1),
                                SetScreenVariable("current_choices", roll_wave_choices(currentPlayer, 3, "normal")),
                            ]
                    elif currentPlayer.dream_shard >= 30 and len(WAVE_REGISTRY) - len(currentPlayer.waves) > 3:
                        textbutton "[[꿈의 파편 30개 소모] 물결 목록 재굴림 (보유: [currentPlayer.dream_shard]개)":
                            text_size 46
                            action [
                                Function(currentPlayer.spend_shard, 30),
                                SetScreenVariable("current_choices", roll_wave_choices(currentPlayer, 3, "normal")),
                            ]


screen arcana_select_ui(arcana_list, title_text="획득할 아르카나(기물)를 선택하세요"):
    modal True
    zorder 100

    add Solid("#05020acc")

    frame:
        xalign 0.5
        yalign 0.5
        xpadding 80
        ypadding 70
        background Solid("#140926f2")
        vbox:
            spacing 45
            xalign 0.5
            text "{font=PyeongChang-Bold.ttf}[title_text]{/font}" size 76 color "#ffffff" xalign 0.5

            hbox:
                spacing 55
                xalign 0.5
                for a in arcana_list:
                    $ card_bg = "#380d17ee" if a.is_cursed else "#24123eee"
                    $ card_hover = "#5c1425ee" if a.is_cursed else "#3e1f6bee"
                    $ tag_col = "#ff5555" if a.is_cursed else "#c184ff"
                    $ tag_label = _("[금기 아르카나]") if a.is_cursed else _("[아르카나 · 기물]")
                    button:
                        xsize 1020
                        ysize 720
                        xpadding 50
                        ypadding 50
                        background Solid(card_bg)
                        hover_background Solid(card_hover)
                        action Return(a)
                        vbox:
                            spacing 24
                            xalign 0.5
                            yalign 0.5
                            text "{font=PyeongChang-Bold.ttf}[tag_label]{/font}" size 48 color tag_col xalign 0.5
                            text "{font=PyeongChang-Bold.ttf}[a.name]{/font}" size 70 color "#ffffff" xalign 0.5 text_align 0.5
                            text "“[a.subtitle]”" size 40 color "#bbbbbb" xalign 0.5 text_align 0.5
                            null height 10
                            text "[a.desc]" size 46 color "#eeeeee" xalign 0.5 text_align 0.5


screen wave_upgrade_ui(cost_per_upgrade=60):
    modal True
    zorder 110

    add Solid("#05020acc")

    frame:
        xalign 0.5
        yalign 0.5
        xsize 2800
        ysize 1650
        xpadding 70
        ypadding 60
        background Solid("#120824f5")
        vbox:
            spacing 30
            hbox:
                xfill True
                if cost_per_upgrade > 0:
                    text "{font=PyeongChang-Bold.ttf}물결 강화 (소모 파편: [cost_per_upgrade]개 / 보유: [currentPlayer.dream_shard]개){/font}" size 64 yalign 0.5
                else:
                    text "{font=PyeongChang-Bold.ttf}강화할 물결을 1개 선택하세요 (무료 강화){/font}" size 64 yalign 0.5
                textbutton "{font=PyeongChang-Bold.ttf}[[닫기]{/font}" action Return("cancel") xalign 1.0 yalign 0.5 text_size 52

            $ upgradable = [w for w in currentPlayer.waves if not w.upgraded]
            if not upgradable:
                null height 200
                text "강화 가능한 미강화 물결이 없습니다." size 54 color "#aaaaaa" xalign 0.5
            else:
                viewport:
                    scrollbars "vertical"
                    mousewheel True
                    draggable True
                    ysize 1300
                    vbox:
                        spacing 25
                        for w in upgradable:
                            $ pinfo = w.path_info
                            $ pcol = pinfo["color"]
                            $ pname = pinfo["name"]
                            $ can_afford = (currentPlayer.dream_shard >= cost_per_upgrade)
                            button:
                                xfill True
                                xpadding 40
                                ypadding 35
                                background Solid("#22103bee")
                                hover_background Solid("#3d1c6bee")
                                sensitive can_afford
                                action Return(w)
                                vbox:
                                    spacing 10
                                    hbox:
                                        spacing 20
                                        text "{font=PyeongChang-Bold.ttf}{color=[pcol]}[[[pname]]{/color} {color=#ffd700}[w.stars_str]{/color} [w.name] → {color=#5ce1e6}[w.name]+{/color}{/font}" size 50
                                    text "{color=#999999}현재: [w.desc_base]{/color}" size 42
                                    text "{color=#5ce1e6}강화: [w.desc_up]{/color}" size 44
