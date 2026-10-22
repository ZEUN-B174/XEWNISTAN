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
screen battle_ui(p=currentPlayer, e=currentEnemy):
    python:
        p_leftbar, p_rightbar = get_bar_colors((p.mp / p.max_mp) * 100 > 20)
        ps_leftbar, ps_rightbar = get_bar_colors(p.sanity > 0)
        e_leftbar, e_rightbar = get_bar_colors((e.mp / e.max_mp) * 100 > 20)

    frame:
        xanchor 0
        yanchor 0
        xpadding 50
        ypadding 50
        xpos 150
        ypos 150
        vbox:
            text "{font=PyeongChang-Bold.ttf}[p.name]{/font}"
            hbox:
                text _('정신력 ')
                bar:
                    value AnimatedValue(p.mp, p.max_mp, 0.2)
                    left_bar Solid(p_leftbar)
                    right_bar Solid(p_rightbar)
                    xalign 0.5
                    xsize 600
                null width 10
                text '[p.mp]/[p.max_mp]'
            hbox:
                if p.sanity > 0:
                    text _("이성치 ")
                else:
                    text _("{color=#cc1100}이성치 {/color}")
                bar:
                    value AnimatedValue(p.sanity + 100, 200, 0.2)
                    left_bar Solid(ps_leftbar)
                    right_bar Solid(ps_rightbar)
                    xalign 0.5
                    xsize 600
                null width 10
                if p.sanity > 0:
                    text '[p.sanity]/100'
                else:
                    text '{color=#cc1100}[p.sanity]/100{/color}'

    # 적 스탯 패널 (우측 상단)
    frame:
        xanchor 1.0
        yanchor 0
        xpadding 50
        ypadding 50
        xpos 3690
        ypos 150
        vbox:
            text "{font=PyeongChang-Bold.ttf}[e.name]{/font}"
            hbox:
                text _('정신력 ')
                bar:
                    value AnimatedValue(e.mp, e.max_mp, 0.2)
                    left_bar Solid(e_leftbar)
                    right_bar Solid(e_rightbar)
                    xalign 0.5
                    xsize 600
                null width 10
                text '[e.mp]/[e.max_mp]'

    # 페이즈 표시
    frame:
        xanchor 0.5
        yanchor 0
        xpadding 50
        ypadding 50
        xpos 0.5
        ypos 150
        vbox:
            text _('페이즈 [phase - len(enemyQueue) + 1]/[phase]')

screen skill_ui(player):
    frame:
        xanchor 1.0
        yanchor 1.0
        xpadding 50
        ypadding 50
        xpos 3690
        ypos 2010
        vbox:
            textbutton "[player.basic_skill.name]" action Return("attack")

            for slot in ("skill", "ultimate", "special_skill"):
                $ active_sk = player.get_active_skill(slot)
                $ sk_cost = active_sk.cost(player)
                if active_sk.is_available(player):
                    if player.is_chaos_slot(slot):
                        textbutton "{font=PyeongChang-Bold.ttf}[active_sk.name] (MP [sk_cost]){/font}" action Return(slot) text_style "mad_button"
                    else:
                        textbutton "[active_sk.name] (MP {color=#7c4dff}[sk_cost]{/color})" action Return(slot)
                else:
                    textbutton "[active_sk.name] (MP 부족)" action NullAction()

label battle(enemyList):
    python:
        on_battle = True
        enemyQueue = []
        phase = random.randint(2, 4)
        for i in range(phase):
            enemyQueue.append(copy.deepcopy(random.choice(enemyList)))
        currentEnemy = enemyQueue[0]

    $ battle_music = random.choice(BATTLE_BGM_LIST)
    play music battle_music fadeout 1.0 fadein 1.0

    show expression currentPlayer.image() as dreamwalker at playerpos zorder 1 with easeinleft
    show expression currentEnemy.image() as nightmare at enemypos zorder 0 with easeinright
    perwin "아참 여기선 아직 자동으로 힐 안되니까 내가 시켜줌"
    $ currentPlayer.mp = currentPlayer.max_mp
    show screen battle_ui with dissolve

    while on_battle:
        $ currentPlayer.sanity_roll()
        call screen skill_ui(currentPlayer)
        $ player_action = _return

        if player_action not in ("attack", "skill", "ultimate", "special_skill"):
            perwin "뭐야ㅅ발 버그제보점;;;"
        else:
            $ chosen_skill = currentPlayer.get_active_skill(player_action)
            if chosen_skill.motion is not None:
                show expression currentPlayer.image_standby() as dreamwalker at chosen_skill.motion
                pause(0.3)

            $ result = currentPlayer.use_skill(player_action, currentEnemy)

            if result.self_effect == "harm":
                play sound (result.self_sound if result.self_sound else "harm.mp3")
                show expression currentPlayer.image_hit() as dreamwalker at hit
                pause(0.3)
            elif result.self_effect == "heal":
                play sound (result.self_sound if result.self_sound else "heal.mp3")
                pause(0.3)

            if result.target_hit:
                show expression currentPlayer.image_attack() as dreamwalker
                play sound result.target_sound
                show expression currentEnemy.image() as nightmare at hit

            pause(0.25)
            show expression currentPlayer.image() as dreamwalker at attack_end
        pause(0.6)

        if currentPlayer.mp <= 0:
            "..."
            $ on_battle = False
            $ player_won = False
        elif currentEnemy.mp <= 0:
            "{color=#7c4dff}[currentEnemy.name]{/color}(을)를 처치했습니다!"
            hide nightmare with dissolve
            $ enemyQueue.pop(0)
            if not enemyQueue:
                $ on_battle = False
                $ player_won = True
            else:
                $ currentEnemy = enemyQueue[0]
                show expression currentEnemy.image() as nightmare at enemypos zorder 0 with easeinright
                "새로운 적이 등장했습니다!"
        else:
            $ enemy_motion = currentEnemy.start_turn()
            if enemy_motion is not None:
                show expression currentEnemy.image() as nightmare at enemy_motion
                pause(0.3)
            $ enemy_result = currentEnemy.take_turn(currentPlayer)
            if enemy_result.target_hit:
                play sound enemy_result.target_sound
                show expression currentPlayer.image_hit() as dreamwalker at hit
                pause(0.25)
                show expression currentPlayer.image() as dreamwalker
            elif enemy_result.self_effect == "heal":
                play sound (enemy_result.self_sound if enemy_result.self_sound else "heal.mp3")
                pause(0.25)
            show expression currentEnemy.image() as nightmare at attack_end

            if currentPlayer.mp <= 0:
                "적에게 쓰러졌습니다..."
                $ on_battle = False
                $ player_won = False

    hide screen battle_ui with dissolve
    hide dreamwalker with easeoutleft
    hide nightmare with easeoutright
    return player_won

