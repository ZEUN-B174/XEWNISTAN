# 이 파일에 게임 스크립트를 입력합니다.
init python:
    import random, copy
    from dataclasses import dataclass, field
    
    # 전역 변수
    totaldamage = 0
    enemyQueue = []
    phase = 0

    # 재화 저장용 전역(?) 플레이어
    @dataclass
    class Player:
        name: str
        level: int = 1
        exp: int = 0
        crystal: int = 0 # 재화

        def getEXP(self, dim, area):
            self.exp += (dim*10 + area)*100
            if self.exp >= 100:
                self.level += self.exp//100
                self.exp %= 100

    @dataclass
    class Tide:
        id: str
        name: str
        description: str

        def when_battle_starts(self, player, enemy):
            pass

        def when_attack(self, player):
            pass
        
        def when_use_skill(self, player):
            pass
        
        def when_use_ultimate(self, player):
            pass

        def when_get_damage(self, player):
            pass

    @dataclass
    class Arcana:
        id: str
        name: str
        description: str

        def on_equip(self, player):
            pass

    @dataclass
    class Nightmare:
        id: str
        name: str
        max_mp: int
        atk: int
        defence: int
        image: str
        mp: int = 0
        turn_counter = 0

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
            damage = amount * (50 / (50 + player.defence))
            return int(damage)

        def heal(self, amount):
            self.mp += amount
            if self.mp > self.max_mp:
                self.mp = self.max_mp

        # 공격 및 스킬(자식 클래스에서 오버라이드)
        def basic_attack(self, player):
            damage = self.attack(player, self.atk)
            player.take_damage(damage)

        def take_turn(self, player):
            self.turn_counter += 1
            self.basic_attack(player)
            return 1

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
                self.basic_attack(player)
                return 1
            else:
                player.take_sanity(5)
                return 2

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
                self.basic_attack(player)
                return 1
            elif self.turn_counter % 3 == 2:
                player.take_sanity(10)
                return 2
            else:
                self.heal(self.atk)
                return 0

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
        crit_damage: int = 1.5
        ideas: int = 200 # 이데아(재화)
        # 리스트(축복/기물) <- 붕스용어잔아... <- 능지딸려서설명할방법이이거박에업서 <- 시@밤쾅
        tides: list = field(default_factory=list) # 물결(축복)
        arcanas: list = field(default_factory=list) # 아르카나(기물) 

        # 노가다 방지용
        def __post_init__(self):
            self.mp = self.max_mp

        # 유틸리티
        def add_arcana(self, artifact):
            self.artifacts.append(artifact)
            artifact.on_equip(self)

        def take_damage(self, amount):
            self.mp -= amount
            if self.mp < 0:
                self.mp = 0

        def take_sanity(self, amount):
            self.sanity -= amount
            if self.sanity < -100:
                self.sanity = -100

        def isInsane(self):
            return 50 - self.sanity//2 > random.randint(1,100)

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
            damage = amount * (50 / (50 + enemy.defence))
            return int(damage)

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

        def meditate(self):
            self.heal(self.atk)

        def skill_name(self):
            return "스킬"
        
        def skill(self, enemy):
            return 1

        def ultimate_name(self):
            return "궁극기"

        def ultimate(self, enemy):
            return 1

    """
    이성치 음수로 내려가면 내려간만큼 이상스킬 발동률/대미지 높아진다고 해야지
    확률형 이상스킬 모션이 애매한데 미리 어떤 행동할지 저장해서 참고하게 할까
    이성치 -50~50으로 할까? 100은 너무 큰거같음
    """

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
            if self.sanity > 0:
                return attack_distance
            else:
                return attack_end

        def ultimate_motion(self):
            if self.sanity > 0:
                return attack_distance
            else:
                return attack_nearby

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
            return f"양자 얽힘 (MP {self.atk//2})" if self.sanity > 0 else f"■해?ㄱ■ (MP {self.atk*2})"

        def skill(self, enemy):
            if self.sanity > 0:
                self.mp -= self.atk//2
                enemy.take_damage(self.attack(enemy, self.atk*2))
                return 1
            else:
                self.harm(self.atk*2)
                self.sanity += 20
                return 2

        def ultimate_name(self):
            return f"양자 폭발 (MP {self.atk*2})" if self.sanity > 0 else f"■■■■■■ (MP {self.atk*3})"

        def ultimate(self, enemy):
            if self.sanity > 0:
                self.mp -= self.atk*2
                enemy.take_damage(self.attack(enemy, self.atk*4))
                return 1
            else:
                self.harm(self.atk*3)
                enemy.take_damage(self.attack(enemy, self.atk*6))
                return 1

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
                text _('페이즈 [len(enemyQueue)]/[phase]')

# image 문을 사용해 이미지를 정의합니다.
image bgplaceholder = "background.png"
image a01 = "placeholder.png"

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
    $ d2 = random.randint(0,1)
    if d2:
        play music "Suicidal Impulse.wav"
    else:
        play music "Suicidal Impulse_var.wav"
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
    perwin "선택지 놔둘테니까 테스트하셈;"
    menu:
        "전투":
            jump area_battle
        "탈주":
            stop music fadeout 1.0
            return

label area_battle:
    call battle([WilloWisp(), Teruterubozu()])
    jump main

label battle(enemyList):
    python:
        on_battle = 1
        enemyQueue = []
        phase = random.randint(2,4)
        for i in range(phase):
            enemyQueue.append(copy.deepcopy(random.choice(enemyList)))
        currentEnemy = enemyQueue[0]

    show expression currentPlayer.image() as dreamwalker at playerpos zorder 1 with easeinleft
    show expression currentEnemy.image as nightmare at enemypos zorder 0 with easeinright
    perwin "아참 여기선 아직 자동으로 힐 안되니까 내가 시켜줌"
    $ currentPlayer.mp = currentPlayer.max_mp
    show screen battle_ui(currentPlayer, currentEnemy) with dissolve
    while on_battle:
        menu choose_skill:
            "행동을 선택하세요"
            "일반 공격" if currentPlayer.sanity != -100:
                show expression currentPlayer.image_standby() as dreamwalker at currentPlayer.attack_motion()
                pause(0.3)

                $ currentPlayer.basic_attack(currentEnemy)
                show expression currentPlayer.image_attack() as dreamwalker
                play sound "attack5.mp3"
                show expression currentEnemy.image as nightmare at hit
                pause(0.25)
                show expression currentPlayer.image() as dreamwalker at attack_end
            # 스킬
            "[currentPlayer.skill_name()]" if currentPlayer.sanity > 0 and currentPlayer.sanity != -100:
                show expression currentPlayer.image_standby() as dreamwalker at currentPlayer.skill_motion()
                pause(0.3)

                $ isEnemyAttacked = currentPlayer.skill(currentEnemy)
                show expression currentPlayer.image_attack() as dreamwalker
                if isEnemyAttacked:
                    play sound "attack5.mp3"
                    show expression currentEnemy.image as nightmare at hit
                pause(0.25)
                show expression currentPlayer.image() as dreamwalker at attack_end
            "{color=#cc1100}{font=PyeongChang-Bold.ttf}[currentPlayer.skill_name()]{/font}{/color}" if currentPlayer.sanity <= 0 and currentPlayer.sanity != -100:
                show expression currentPlayer.image_standby() as dreamwalker at currentPlayer.skill_motion()
                pause(0.3)

                $ isEnemyAttacked = currentPlayer.skill(currentEnemy)
                show expression currentPlayer.image_attack() as dreamwalker
                if isEnemyAttacked:
                    play sound "attack5.mp3"
                    if isEnemyAttacked == 2:
                        show expression currentPlayer.image_hit() as dreamwalker at hit
                    else:
                        show expression currentEnemy.image as nightmare at hit
                pause(0.25)
                show expression currentPlayer.image() as dreamwalker at attack_end
            # 궁극기
            "[currentPlayer.ultimate_name()]" if currentPlayer.sanity > 0 and currentPlayer.sanity != -100:
                show expression currentPlayer.image_standby() as dreamwalker at currentPlayer.ultimate_motion()
                pause(0.3)

                $ isEnemyAttacked = currentPlayer.ultimate(currentEnemy)
                show expression currentPlayer.image_attack() as dreamwalker
                if isEnemyAttacked:
                    play sound "attack5.mp3"
                    show expression currentEnemy.image as nightmare at hit
                pause(0.25)
                show expression currentPlayer.image() as dreamwalker at attack_end
            "{color=#cc1100}{font=PyeongChang-Bold.ttf}[currentPlayer.ultimate_name()]{/font}{/color}" if currentPlayer.sanity <= 0 and currentPlayer.sanity != -100:
                show expression currentPlayer.image_standby() as dreamwalker at currentPlayer.ultimate_motion()
                pause(0.3)

                $ isEnemyAttacked = currentPlayer.ultimate(currentEnemy)
                show expression currentPlayer.image_attack() as dreamwalker
                if isEnemyAttacked:
                    play sound "attack5.mp3"
                    show expression currentEnemy.image as nightmare at hit
                pause(0.25)
                show expression currentPlayer.image() as dreamwalker at attack_end
            
            "명상" if currentPlayer.sanity != -100:
                $ currentPlayer.meditate()
                play sound "heal.mp3"
            "{color=#cc1100}{font=PyeongChang-Bold.ttf}자■하?ㄱ■{/font}{/color}" if currentPlayer.sanity == -100:
                $ currentPlayer.mp = 0
                play sound "attack5.mp3"
                show expression currentPlayer.image_hit() as dreamwalker at hit
                pause(0.25)
                show expression currentPlayer.image() as dreamwalker
        pause(0.6)

        if currentPlayer.mp <= 0:
            "..."
            $ on_battle = 0
            hide screen battle_ui with dissolve
            hide dreamwalker with easeoutleft
            hide nightmare with easeoutright
            return
        
        if currentEnemy.mp <= 0:
            "{color=#7c4dff}[currentEnemy.name]{/color}(을)를 처치했습니다!"
            hide nightmare with dissolve
            $ enemyQueue.pop(0)
            if not enemyQueue:
                $ on_battle = 0
            else:
                $ currentEnemy = enemyQueue[0]
                show expression currentEnemy.image as nightmare at right zorder 0 with easeinright
                show screen battle_ui(currentPlayer, currentEnemy) with dissolve
                "새로운 적이 등장했습니다!"
        else:
            show expression currentEnemy.image as nightmare at currentEnemy.turn_motion()
            pause(0.3)
            $ isPlayerAttacked = currentEnemy.take_turn(currentPlayer)
            if isPlayerAttacked == 1:
                play sound "attack4.mp3"
                show expression currentPlayer.image_hit() as dreamwalker at hit
                pause(0.25)
                show expression currentPlayer.image() as dreamwalker
            elif isPlayerAttacked == 2:
                play sound "dark_magic.mp3"
                show expression currentPlayer.image_hit() as dreamwalker at hit
                pause(0.25)
                show expression currentPlayer.image() as dreamwalker
            else:
                play sound "heal.mp3"
                pause(0.25)
            show expression currentEnemy.image as nightmare at attack_end


        if currentPlayer.mp <= 0:
            "적에게 쓰러졌습니다..."
            $ on_battle = 0
    hide screen battle_ui with dissolve
    hide dreamwalker with easeoutleft
    hide nightmare with easeoutright
    return