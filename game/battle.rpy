default enemyQueue = []
default phase = 0
default currentPlayer = None
default currentEnemy = None
default on_battle = False
default player_won = False

init python:
    import random, copy

    def get_bar_colors(is_normal):
        if is_normal:
            return ('#c184ff', '#3d1466')
        return ('#cc1100', '#4c0f14')

    BATTLE_BGM_LIST = [
        "<volume 0.5>Shanty of Charon.wav",
        "Suicidal Impulse.wav",
        "Suicidal Impulse_var.wav",
        "<volume 0.5>Inception.wav",
        "<volume 0.5>Cipher.wav",
        "<volume 0.5>Euthanize.wav",
    ]

# 스타일
style mad_button:
    idle_color "#8c0909"
    hover_color "#cc1100"

# 위치/변형
transform playerpos:
    xanchor 0.5
    yanchor 1.0
    xpos 720
    ypos 1.0

transform enemypos:
    xanchor 0.5
    yanchor 1.0
    xpos 3120
    ypos 1.0

transform hit:
    linear 0.05 xoffset -70
    linear 0.05 xoffset 70
    linear 0.05 xoffset -35
    linear 0.05 xoffset 35
    linear 0.05 xoffset 0

# 캐릭터 모션 정의
transform attack_nearby:
    ease 0.3 xoffset 1900

transform attack_distance:
    easein 0.2 xoffset -200

transform attack_delayed_nearby:
    linear 0.25 xoffset 0
    ease 0.3 xoffset 1900

transform attack_end:
    ease 0.3 xoffset 0

# 적 모션 정의
transform enemy_attack_nearby:
    ease 0.3 xoffset -1900

transform enemy_attack_distance:
    easein 0.2 xoffset 200

# UI
screen player_status_panel(p):
    python:
        p_leftbar, p_rightbar = get_bar_colors((p.mp / p.max_mp) * 100 > 20)
        ps_leftbar, ps_rightbar = get_bar_colors(p.sanity > 0)

    frame:
        xanchor 0.0
        yanchor 0.0
        xpos 80
        ypos 80
        xpadding 45
        ypadding 45
        vbox:
            spacing 12
            hbox:
                text "{font=PyeongChang-Bold.ttf}[p.name]{/font}" size 60 yalign 0.5
                if on_battle and p.isInsane:
                    spacing 12
                    text "{color=#cc1100}{font=PyeongChang-Bold.ttf}[[광기]{/font}{/color}" size 46 yalign 0.5
                textbutton "{color=#c184ff}[[상세 정보]{/color}" action Show("character_detail_ui", p=p) text_size 44 yalign 0.5
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
                    text _("{color=#cc1100}이성치{/color}") size 48 yalign 0.5
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
                    text "{color=#cc1100}[p.sanity]/100{/color}" size 48 yalign 0.5
            if p.buffs:
                hbox:
                    spacing 15
                    for b in p.buffs:
                        if b.is_debuff:
                            text "{color=#cc1100}[[[b.name] [b.duration]턴]{/color}" size 40
                        else:
                            text "{color=#c184ff}[[[b.name] [b.duration]턴]{/color}" size 40


screen character_detail_ui(p):
    modal True
    zorder 150
    default show_chaos_skills = (p.sanity <= 0)

    python:
        def_mitigation = int(round((1.0 - (DEFENCE_CONSTANT / (DEFENCE_CONSTANT + max(0, p.eff_defence)))) * 100))
        crit_dmg_pct = int(round(p.eff_crit_damage * 100))

    add Solid("#000000aa")

    frame:
        xalign 0.5
        yalign 0.5
        xpadding 70
        ypadding 70
        vbox:
            spacing 35
            hbox:
                xfill True
                text "{font=PyeongChang-Bold.ttf}[p.name] — 상세 상태 및 스킬 정보{/font}" size 68 yalign 0.5
                textbutton "{font=PyeongChang-Bold.ttf}[[닫기]{/font}" action Hide("character_detail_ui") xalign 1.0 yalign 0.5 text_size 52

            hbox:
                spacing 80
                # 좌측: 세부 스탯
                vbox:
                    spacing 18
                    xsize 1050
                    text "{font=PyeongChang-Bold.ttf}{color=#c184ff}■ 세부 스탯{/color}{/font}" size 54
                    null height 5
                    text "정신력: [p.mp] / [p.max_mp]" size 46
                    if p.sanity > 0:
                        text "이성치: [p.sanity] / 100 (정상)" size 46
                    else:
                        text "이성치: {color=#cc1100}[p.sanity] / 100 (침식 상태){/color}" size 46
                    if on_battle:
                        if p.isInsane:
                            text "현재 턴 광기 판정: {color=#cc1100}발동 (혼돈 스킬 활성화){/color}" size 44
                        else:
                            text "현재 턴 광기 판정: 미발동" size 44 color "#aaaaaa"

                    if p.eff_atk != p.atk:
                        text "공격력: {color=#c184ff}[p.eff_atk]{/color} (기본 [p.atk])" size 46
                    else:
                        text "공격력: [p.eff_atk]" size 46

                    if p.eff_defence != p.defence:
                        text "방어력: {color=#c184ff}[p.eff_defence]{/color} (기본 [p.defence] / 피해 감쇄 [def_mitigation]%)" size 46
                    else:
                        text "방어력: [p.eff_defence] (피해 감쇄 [def_mitigation]%)" size 46

                    text "치명타 확률: [p.eff_crit_chance]%" size 46
                    text "치명타 피해: [crit_dmg_pct]% ([p.eff_crit_damage]배)" size 46
                    text "보유 꿈의 파편: {color=#c184ff}[p.dream_shard]개{/color}" size 46
                    if playerAccount is not None:
                        text "자각몽 동조 레벨: Lv.[playerAccount.level] (EXP [playerAccount.exp]/100)" size 44 color "#cccccc"

                    null height 10
                    text "{font=PyeongChang-Bold.ttf}{color=#c184ff}■ 적용 중인 효과{/color}{/font}" size 50
                    if p.buffs:
                        vbox:
                            spacing 8
                            for b in p.buffs:
                                if b.is_debuff:
                                    text "{color=#cc1100}• [[디버프] [b.name] (남은 턴: [b.duration]){/color}" size 42
                                else:
                                    text "{color=#c184ff}• [[버프] [b.name] (남은 턴: [b.duration]){/color}" size 42
                    else:
                        text "적용 중인 버프/디버프 없음" size 42 color "#888888"

                # 우측: 스킬 목록 및 설명
                vbox:
                    spacing 20
                    xsize 1650
                    hbox:
                        spacing 30
                        text "{font=PyeongChang-Bold.ttf}{color=#c184ff}■ 보유 스킬 정보{/color}{/font}" size 54 yalign 0.5
                        textbutton ("{color=#ffffff}[[일반 스킬]{/color}" if not show_chaos_skills else "[[일반 스킬]") action SetScreenVariable("show_chaos_skills", False) text_size 44 yalign 0.5
                        textbutton ("{color=#cc1100}[[혼돈 스킬]{/color}" if show_chaos_skills else "[[혼돈 스킬]") action SetScreenVariable("show_chaos_skills", True) text_size 44 yalign 0.5

                    if not show_chaos_skills:
                        $ skill_entries = [
                            ("일반 공격", p.basic_skill, False),
                            ("일반 스킬", p.skill_normal, False),
                            ("궁극기", p.ultimate_normal, False),
                            ("특수 스킬", p.special_normal, False),
                        ]
                    else:
                        $ skill_entries = [
                            ("일반 공격 (공통)", p.basic_skill, False),
                            ("일반 스킬 (광기 발동 시)", p.skill_chaos, True),
                            ("궁극기 (광기 발동 시)", p.ultimate_chaos, True),
                            ("특수 스킬 (이성치 0 이하 시)", p.special_chaos, True),
                        ]

                    for slot_label, sk_obj, is_chaos in skill_entries:
                        if sk_obj is not None:
                            $ sk_c = sk_obj.cost(p)
                            vbox:
                                spacing 6
                                if is_chaos:
                                    text "{font=PyeongChang-Bold.ttf}{color=#cc1100}[[[slot_label]] [sk_obj.name]{/color}{/font}  (소모 정신력: [sk_c])" size 46
                                else:
                                    text "{font=PyeongChang-Bold.ttf}{color=#c184ff}[[[slot_label]]{/color} [sk_obj.name]{/font}  (소모 정신력: [sk_c])" size 46
                                text "[sk_obj.desc]" size 40 color "#dddddd"

    key "game_menu" action Hide("character_detail_ui")


screen battle_ui(p=currentPlayer, e=currentEnemy):
    zorder 50
    python:
        e_leftbar, e_rightbar = get_bar_colors((e.mp / e.max_mp) * 100 > 20)

    use player_status_panel(p)

    # 적 스탯 패널 (우측 상단)
    frame:
        xanchor 1.0
        yanchor 0.0
        xpos 3760
        ypos 80
        xpadding 45
        ypadding 45
        vbox:
            spacing 12
            hbox:
                spacing 25
                xalign 1.0
                text "{font=PyeongChang-Bold.ttf}[e.name]{/font}" size 60 yalign 0.5
                text "공격력 [e.eff_atk] / 방어력 [e.eff_defence]" size 46 color "#cccccc" yalign 0.5
            hbox:
                spacing 15
                xalign 1.0
                text _('정신력') size 48 yalign 0.5
                bar:
                    value AnimatedValue(e.mp, e.max_mp, 0.2)
                    left_bar Solid(e_leftbar)
                    right_bar Solid(e_rightbar)
                    xsize 520
                    ysize 48
                    yalign 0.5
                text '[e.mp]/[e.max_mp]' size 48 yalign 0.5
            if e.buffs:
                hbox:
                    spacing 15
                    xalign 1.0
                    for b in e.buffs:
                        if b.is_debuff:
                            text "{color=#cc1100}[[[b.name] [b.duration]턴]{/color}" size 40
                        else:
                            text "{color=#c184ff}[[[b.name] [b.duration]턴]{/color}" size 40

    # 페이즈 표시 (중앙 상단)
    frame:
        xanchor 0.5
        yanchor 0.0
        xpadding 45
        ypadding 45
        xpos 0.5
        ypos 80
        vbox:
            text _('페이즈 [phase - len(enemyQueue) + 1] / [phase]') size 52


screen skill_ui(player):
    default hovered_slot = None

    if hovered_slot is not None:
        $ h_sk = player.get_active_skill(hovered_slot)
        $ h_cost = h_sk.cost(player)
        $ h_chaos = player.is_chaos_slot(hovered_slot)
        frame:
            xanchor 1.0
            yanchor 1.0
            xpos 3690
            ypos 1410
            xsize 1150
            xpadding 45
            ypadding 45
            vbox:
                spacing 10
                if h_chaos:
                    text "{font=PyeongChang-Bold.ttf}{color=#cc1100}[h_sk.name]{/color}{/font}  (소모 정신력: [h_cost])" size 50
                else:
                    text "{font=PyeongChang-Bold.ttf}[h_sk.name]{/font}  (소모 정신력: {color=#c184ff}[h_cost]{/color})" size 50
                text "[h_sk.desc]" size 42 color "#dddddd"

    frame:
        xanchor 1.0
        yanchor 1.0
        xpadding 50
        ypadding 50
        xpos 3690
        ypos 2010
        vbox:
            $ basic_cost = player.basic_skill.cost(player)
            textbutton "[player.basic_skill.name] (정신력 {color=#7c4dff}[basic_cost]{/color})":
                action Return("attack")
                hovered SetScreenVariable("hovered_slot", "attack")
                unhovered SetScreenVariable("hovered_slot", None)

            for slot in ("skill", "ultimate", "special_skill"):
                $ active_sk = player.get_active_skill(slot)
                $ sk_cost = active_sk.cost(player)
                if active_sk.is_available(player):
                    if player.is_chaos_slot(slot):
                        textbutton "{font=PyeongChang-Bold.ttf}[active_sk.name] (정신력 [sk_cost]){/font}":
                            action Return(slot)
                            text_style "mad_button"
                            hovered SetScreenVariable("hovered_slot", slot)
                            unhovered SetScreenVariable("hovered_slot", None)
                    else:
                        textbutton "[active_sk.name] (정신력 {color=#7c4dff}[sk_cost]{/color})":
                            action Return(slot)
                            hovered SetScreenVariable("hovered_slot", slot)
                            unhovered SetScreenVariable("hovered_slot", None)
                else:
                    textbutton "{color=#888888}[active_sk.name] (정신력 [sk_cost] / 부족){/color}":
                        action NullAction()
                        hovered SetScreenVariable("hovered_slot", slot)
                        unhovered SetScreenVariable("hovered_slot", None)

label battle(enemyList, phase_count=None):
    python:
        on_battle = True
        battle_active = True
        currentPlayer.clear_buffs()
        enemyQueue = []
        if phase_count is not None:
            phase = phase_count
        else:
            phase = random.randint(2, 3)
        for i in range(phase):
            enemyQueue.append(copy.deepcopy(random.choice(enemyList)))
        currentEnemy = enemyQueue[0]

    $ battle_music = random.choice(BATTLE_BGM_LIST)
    play music battle_music fadeout 1.0 fadein 1.0

    show expression currentPlayer.image() as dreamwalker at playerpos zorder 1 with easeinleft
    show expression currentEnemy.image() as nightmare at enemypos zorder 0 with easeinright
    show screen battle_ui with dissolve

    while battle_active:
        $ currentPlayer.sanity_roll()
        call screen skill_ui(currentPlayer)
        $ player_action = _return

        if player_action not in ("attack", "skill", "ultimate", "special_skill"):
            perwin "뭐야ㅅ발 버그제보점;;;"
        else:
            $ fx = currentPlayer.use_skill(player_action, currentEnemy)
            if fx.motion is not None:
                show expression currentPlayer.image_standby() as dreamwalker at fx.motion
                pause(0.3)

            if fx.self_action is not None:
                $ fx.self_action()

            if fx.self_effect == "harm":
                play sound (fx.self_sound if fx.self_sound else "harm.mp3")
                show expression currentPlayer.image_hit() as dreamwalker at hit
                pause(0.3)
            elif fx.self_effect in ("heal", "buff"):
                play sound (fx.self_sound if fx.self_sound else "heal.mp3")
                pause(0.3)
            elif fx.self_effect == "debuff":
                play sound (fx.self_sound if fx.self_sound else "dark_magic.mp3")
                pause(0.3)

            $ total_hits = fx.total_hits()
            if total_hits > 0:
                show expression currentPlayer.image_attack() as dreamwalker
                $ hit_idx = 0
                while hit_idx < total_hits:
                    $ fx.apply_hit(hit_idx)
                    play sound fx.target_sound
                    show expression currentEnemy.image() as nightmare at hit
                    pause(fx.hit_interval)
                    $ hit_idx += 1
            elif fx.target_effect is not None:
                $ fx.apply_hit(0)
                play sound (fx.target_sound if fx.target_sound else "dark_magic.mp3")
                pause(0.25)

            show expression currentPlayer.image() as dreamwalker at attack_end
            $ currentPlayer.tick_buffs()
        pause(0.6)

        if currentPlayer.mp <= 0:
            "..."
            $ battle_active = False
            $ player_won = False
        elif currentEnemy.mp <= 0:
            "{color=#7c4dff}[currentEnemy.name]{/color}(을)를 처치했습니다!"
            hide nightmare with dissolve
            $ enemyQueue.pop(0)
            if not enemyQueue:
                $ battle_active = False
                $ player_won = True
            else:
                $ currentEnemy = enemyQueue[0]
                show expression currentEnemy.image() as nightmare at enemypos zorder 0 with easeinright
                "새로운 적이 등장했습니다!"
        else:
            $ enemy_fx = currentEnemy.act_turn(currentPlayer)
            if enemy_fx.motion is not None:
                show expression currentEnemy.image() as nightmare at enemy_fx.motion
                pause(0.3)

            if enemy_fx.self_action is not None:
                $ enemy_fx.self_action()

            if enemy_fx.self_effect == "harm":
                play sound (enemy_fx.self_sound if enemy_fx.self_sound else "harm.mp3")
                show expression currentEnemy.image() as nightmare at hit
                pause(0.25)
            elif enemy_fx.self_effect in ("heal", "buff"):
                play sound (enemy_fx.self_sound if enemy_fx.self_sound else "heal.mp3")
                pause(0.25)
            elif enemy_fx.self_effect == "debuff":
                play sound (enemy_fx.self_sound if enemy_fx.self_sound else "dark_magic.mp3")
                pause(0.25)

            $ enemy_hits = enemy_fx.total_hits()
            if enemy_hits > 0:
                $ hit_idx = 0
                while hit_idx < enemy_hits:
                    $ enemy_fx.apply_hit(hit_idx)
                    play sound enemy_fx.target_sound
                    show expression currentPlayer.image_hit() as dreamwalker at hit
                    pause(enemy_fx.hit_interval)
                    $ hit_idx += 1
                show expression currentPlayer.image() as dreamwalker
            elif enemy_fx.target_effect is not None:
                $ enemy_fx.apply_hit(0)
                play sound (enemy_fx.target_sound if enemy_fx.target_sound else "dark_magic.mp3")
                pause(0.25)

            show expression currentEnemy.image() as nightmare at attack_end
            $ currentEnemy.tick_buffs()

            if currentPlayer.mp <= 0:
                "적에게 쓰러졌습니다..."
                $ battle_active = False
                $ player_won = False

    $ currentPlayer.clear_buffs()
    hide screen battle_ui with dissolve
    hide dreamwalker with easeoutleft
    hide nightmare with easeoutright
    $ on_battle = False
    return player_won