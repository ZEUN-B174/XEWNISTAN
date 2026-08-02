# 이 파일에 게임 스크립트를 입력합니다.
default enemyQueue = []
default phase = 0
default currentPlayer = None
default currentEnemy = None
default on_battle = False
default player_won = False

init python:
    import random, copy
    from dataclasses import dataclass

    # 방어력에 따른 데미지 감쇄 상수. 이 값만큼 방어력이 있으면 피해량이 절반이 됨.
    DEFENCE_CONSTANT = 50

    def calc_damage(amount, target_defence):
        return int(amount * (DEFENCE_CONSTANT / (DEFENCE_CONSTANT + target_defence)))

    @dataclass
    class Player:
        level: int = 1
        exp: int = 0
        dream_crystal: int = 0 # 영구 재화 (꿈의 결정)

        def getEXP(self, dim, area):
            self.exp += (dim*10 + area)*100
            if self.exp >= 100:
                self.level += self.exp//100
                self.exp %= 100

    @dataclass
    class ActionResult:
        """
        공격/스킬/턴 처리 결과로 리턴하는 객체.
        battle 루프는 이 값만 보고 연출(모션/사운드)을 결정하기 때문에,
        새 스킬을 추가할 때 battle 루프를 건드릴 필요가 없어짐.
        """
        target_hit: bool = False        # 상대(적 또는 플레이어)에게 피격 연출을 보여줄지
        target_sound: str = "attack5.mp3"
        self_effect: str = None         # None / "heal" / "harm" — 시전자 본인에게 일어나는 연출
        self_sound: str = None

    @dataclass
    class Nightmare:
        id: str
        name: str
        max_mp: int
        atk: int
        defence: int
        image: str
        mp: int = 0
        turn_counter: int = 0

        def __post_init__(self):
            self.mp = self.max_mp

        def take_damage(self, amount):
            self.mp -= amount
            if self.mp < 0:
                self.mp = 0

        # 적 모션
        def turn_motion(self):
            return enemy_attack_nearby

        # 기본기능
        def attack(self, player, amount):
            return calc_damage(amount, player.defence)

        def heal(self, amount):
            self.mp += amount
            if self.mp > self.max_mp:
                self.mp = self.max_mp

        # 공격 및 스킬(자식 클래스에서 오버라이드)
        def basic_attack(self, player):
            damage = self.attack(player, self.atk)
            player.take_damage(damage)
            return ActionResult(target_hit=True, target_sound="attack4.mp3")

        def take_turn(self, player):
            self.turn_counter += 1
            return self.basic_attack(player)

    @dataclass
    class WilloWisp(Nightmare):
        id: str = "willowisp"
        name: str = _("도깨비불")
        max_mp: int = 50
        atk: int = 5
        defence: int = 5
        image: str = "willowisp.png"

        def turn_motion(self):
            if (self.turn_counter + 1) % 2:
                return enemy_attack_nearby
            else:
                return enemy_attack_distance

        def take_turn(self, player):
            self.turn_counter += 1
            if self.turn_counter % 2:
                return self.basic_attack(player)
            else:
                player.take_sanity(5)
                return ActionResult(target_hit=True, target_sound="dark_magic.mp3")

    @dataclass
    class Teruterubozu(Nightmare):
        id: str = "teruterubozu"
        name: str = _("테루테루보즈")
        max_mp: int = 30
        atk: int = 10
        defence: int = 5
        image: str = "teruterubozu.png"

        def turn_motion(self):
            if (self.turn_counter + 1) % 3 == 1:
                return enemy_attack_distance
            elif (self.turn_counter + 1) % 3 == 2:
                return enemy_attack_distance
            else:
                return attack_end

        def take_turn(self, player):
            self.turn_counter += 1
            if self.turn_counter % 3 == 1:
                return self.basic_attack(player)
            elif self.turn_counter % 3 == 2:
                player.take_sanity(10)
                return ActionResult(target_hit=True, target_sound="dark_magic.mp3")
            else:
                self.heal(self.atk)
                return ActionResult(self_effect="heal", self_sound="heal.mp3")

    @dataclass
    class Dreamwalker:
        id: str
        name: str
        max_mp: int
        sanity: int
        atk: int
        defence: int
        # 여기서부터 미리 정의해두는
        mp: int = 0
        crit_chance: int = 20
        crit_damage: float = 1.5
        dream_shard: int = 200 # 재화 (꿈의 파편)
        isInsane: bool = False 

        # 노가다 방지용
        def __post_init__(self):
            self.mp = self.max_mp

        # 유틸리티
        def take_damage(self, amount):
            self.mp -= amount
            if self.mp < 0:
                self.mp = 0

        def take_sanity(self, amount):
            self.sanity -= amount
            if self.sanity < -100:
                self.sanity = -100

        def recover_sanity(self, amount):
            self.sanity += amount
            if self.sanity > 100:
                self.sanity = 100

        def sanity_roll(self):
            if self.sanity > 0 or self.sanity*-1 < random.randint(1,100):
                self.isInsane = False
            else:
                self.isInsane = True

        # 이미지
        def image(self):
            return "charactername.png"

        def image_standby(self):
            return "charactername_standby.png"

        def image_attack(self):
            return "charactername_attack.png"

        def image_hit(self):
            return "charactername_hit.png"

        # 캐릭터 모션
        def attack_motion(self):
            return attack_nearby

        def skill_motion(self):
            return attack_distance

        def ultimate_motion(self):
            return attack_distance

        # 기본기능
        def attack(self, enemy, amount):
            return calc_damage(amount, enemy.defence)

        def heal(self, amount):
            self.mp += amount
            if self.mp > self.max_mp:
                self.mp = self.max_mp

        def harm(self, amount):
            self.mp -= amount
            if self.mp <= 0:
                self.mp = 1

        # 공격 및 스킬(자식 클래스에서 오버라이드)
        def basic_attack(self, enemy):
            damage = self.attack(enemy, self.atk)
            enemy.take_damage(damage)
            return ActionResult(target_hit=True)

        def meditate(self):
            self.heal(self.atk)
            return ActionResult(self_effect="heal", self_sound="heal.mp3")

        def skill_name(self):
            return "스킬"

        def skill_cost(self):
            return self.atk//2

        def skill(self, enemy):
            return ActionResult()

        def ultimate_name(self):
            return "궁극기"

        def ultimate_cost(self):
            return self.atk*2

        def ultimate(self, enemy):
            return ActionResult()

    # 캐릭터
    @dataclass
    class Tester(Dreamwalker):
        """
        밸런스형 딜러. 일반 상태에서는 평범한 딜러지만 광기 상태에서는 자해딜러가 된다.
        """
        id: str = "tester"
        name: str = "테스터"
        max_mp: int = 100
        sanity: int = 100
        atk: int = 10
        defence: int = 10

        # 스킬 모션
        def skill_motion(self):
            if self.isInsane:
                return attack_end
            else:
                return attack_distance

        def ultimate_motion(self):
            if self.isInsane:
                return attack_delayed_nearby
            else:
                return attack_distance

        # 이미지
        def image(self):
            return "tester.png"

        def image_standby(self):
            return "tester.png"

        def image_attack(self):
            return "tester_attack.png"

        def image_hit(self):
            return "tester_hit.png"

        # 스킬
        def skill_name(self):
            return "자해" if self.isInsane else "양자 얽힘"

        def skill_cost(self):
            if self.isInsane:
                return self.atk*2
            else:
                return self.atk//2

        def skill(self, enemy):
            if self.isInsane:
                self.harm(self.atk*2)
                self.recover_sanity(20)
                return ActionResult(self_effect="harm", self_sound="harm.mp3")
            else:
                self.mp -= self.atk//2
                enemy.take_damage(self.attack(enemy, self.atk*2))
                return ActionResult(target_hit=True)

        def ultimate_name(self):
            return "■미■ㅋ#■ㅔ" if self.isInsane else "양자 폭발"

        def ultimate_cost(self):
            if self.isInsane:
                return self.atk*3
            else:
                return self.atk*2

        def ultimate(self, enemy):
            if self.isInsane:
                self.harm(self.atk*3)
                enemy.take_damage(self.attack(enemy, self.atk*6))
                return ActionResult(target_hit=True, self_effect="harm", self_sound="harm.mp3")
            else:
                self.mp -= self.atk*2
                enemy.take_damage(self.attack(enemy, self.atk*4))
                return ActionResult(target_hit=True)
# 스타일
style mad_button:
    idle_color "#8c0909"
    hover_color "#cc1100"

# UI
screen battle_ui(p, e):
    python:
        if (p.mp/p.max_mp)*100 > 20:
            p_leftbar = '#c184ff'
            p_rightbar = '#3d1466'
        else:
            p_leftbar = '#cc1100'
            p_rightbar = '#4c0f14'

        if p.sanity > 0:
            ps_leftbar = '#c184ff'
            ps_rightbar = '#3d1466'
        else:
            ps_leftbar = '#cc1100'
            ps_rightbar = '#4c0f14'

        if (e.mp/e.max_mp)*100 > 20:
            e_leftbar = '#c184ff'
            e_rightbar = '#3d1466'
        else:
            e_leftbar = '#cc1100'
            e_rightbar = '#4c0f14'

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
                    value AnimatedValue(p.sanity+100, 200, 0.2)
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
            textbutton "일반 공격" action Return("attack")
            if player.isInsane:
                    textbutton "{font=PyeongChang-Bold.ttf}[player.skill_name()] (MP [player.skill_cost()]){/font}" action Return("skill") text_style "mad_button"
                    textbutton "{font=PyeongChang-Bold.ttf}[player.ultimate_name()] (MP [player.ultimate_cost()]){/font}" action Return("ultimate") text_style "mad_button"
            else:
                if player.skill_cost() < player.mp:
                    textbutton "[player.skill_name()] (MP {color=#7c4dff}[player.skill_cost()]{/color})" action Return("skill")
                else:
                    textbutton "[player.skill_name()] (MP 부족)" action NullAction()
                if player.ultimate_cost() < player.mp:
                    textbutton "[player.ultimate_name()] (MP {color=#7c4dff}[player.ultimate_cost()]{/color})" action Return("ultimate")
                else:
                    textbutton "[player.ultimate_name()] (MP 부족)" action NullAction()
            textbutton "명상" action Return("meditate")

# image 문을 사용해 이미지를 정의합니다.
image bgplaceholder = "background.png"

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

label battle(enemyList):
    python:
        on_battle = True
        enemyQueue = []
        phase = random.randint(2,4)
        for i in range(phase):
            enemyQueue.append(copy.deepcopy(random.choice(enemyList)))
        currentEnemy = enemyQueue[0]
    $ battle_music = random.randint(1,6)
    if battle_music == 1:
        play music "Shanty of Charon.wav" volume 0.5 fadeout 1.0 fadein 1.0
    elif battle_music == 2:
        play music "Suicidal Impulse.wav" fadeout 1.0 fadein 1.0
    elif battle_music == 3:
        play music "Suicidal Impulse_var.wav" fadeout 1.0 fadein 1.0
    elif battle_music == 4:
        play music "Inception.wav" volume 0.5 fadeout 1.0 fadein 1.0
    elif battle_music == 5:
        play music "Cipher.wav" volume 0.5 fadeout 1.0 fadein 1.0
    else:
        play music "Euthanize.wav" volume 0.5 fadeout 1.0 fadein 1.0
    
    show expression currentPlayer.image() as dreamwalker at playerpos zorder 1 with easeinleft
    show expression currentEnemy.image as nightmare at enemypos zorder 0 with easeinright
    perwin "아참 여기선 아직 자동으로 힐 안되니까 내가 시켜줌"
    $ currentPlayer.mp = currentPlayer.max_mp
    show screen battle_ui(currentPlayer, currentEnemy) with dissolve
    while on_battle:
        $ currentPlayer.sanity_roll()
        call screen skill_ui(currentPlayer)
        $ player_action = _return

        if player_action == "attack":
            show expression currentPlayer.image_standby() as dreamwalker at currentPlayer.attack_motion()
        elif player_action == "skill":
            show expression currentPlayer.image_standby() as dreamwalker at currentPlayer.skill_motion()
        elif player_action == "ultimate":
            show expression currentPlayer.image_standby() as dreamwalker at currentPlayer.ultimate_motion()
        elif player_action == "meditate":
            $ result = currentPlayer.meditate()
            play sound "heal.mp3"
        else:
            perwin "뭐야ㅅ발 버그제보점;;;"
            $ result = ActionResult()

        if player_action in ("attack", "skill", "ultimate"):
            pause(0.3)
            if player_action == "attack":
                $ result = currentPlayer.basic_attack(currentEnemy)
            elif player_action == "skill":
                $ result = currentPlayer.skill(currentEnemy)
            elif player_action == "ultimate":
                $ result = currentPlayer.ultimate(currentEnemy)

            if result.self_effect == "harm":
                play sound (result.self_sound if result.self_sound else "harm.mp3")
                show expression currentPlayer.image_hit() as dreamwalker at hit
                pause(0.3)
            if result.target_hit:
                show expression currentPlayer.image_attack() as dreamwalker
                play sound result.target_sound
                show expression currentEnemy.image as nightmare at hit
            pause(0.25)
            show expression currentPlayer.image() as dreamwalker at attack_end
        pause(0.6)
        
        if currentEnemy.mp <= 0:
            "{color=#7c4dff}[currentEnemy.name]{/color}(을)를 처치했습니다!"
            hide nightmare with dissolve
            $ enemyQueue.pop(0)
            if not enemyQueue:
                $ on_battle = False
                $ player_won = True
            else:
                $ currentEnemy = enemyQueue[0]
                show expression currentEnemy.image as nightmare at enemypos zorder 0 with easeinright
                show screen battle_ui(currentPlayer, currentEnemy) with dissolve
                "새로운 적이 등장했습니다!"
        else:
            show expression currentEnemy.image as nightmare at currentEnemy.turn_motion()
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
            show expression currentEnemy.image as nightmare at attack_end


        if currentPlayer.mp <= 0:
            "적에게 쓰러졌습니다..."
            $ on_battle = False
            $ player_won = False
    hide screen battle_ui with dissolve
    hide dreamwalker with easeoutleft
    hide nightmare with easeoutright
    return player_won