init 2 python:
    import random
    from dataclasses import dataclass

    @dataclass
    class Player:
        level: int = 1
        exp: int = 0
        dream_crystal: int = 0 # 영구 재화 (꿈의 결정)

        def getEXP(self, dim, area):
            self.exp += (dim * 10 + area) * 100
            if self.exp >= 100:
                self.level += self.exp // 100
                self.exp %= 100

    @dataclass
    class Unit:
        """플레이어 캐릭터(Dreamwalker)와 적(Nightmare)의 공통 부모 클래스"""
        id: str = ""
        name: str = ""
        max_mp: int = 100
        atk: int = 10
        defence: int = 10
        mp: int = 0
        crit_chance: int = 0
        crit_damage: float = 1.5

        def __post_init__(self):
            self.mp = self.max_mp

        def take_damage(self, amount):
            self.mp = max(0, self.mp - amount)

        def heal(self, amount):
            self.mp = min(self.max_mp, self.mp + amount)

        def attack(self, target, amount):
            if self.crit_chance > 0 and random.randint(1, 100) <= self.crit_chance:
                amount = amount * self.crit_damage
            return calc_damage(amount, target.defence)

        def image(self):
            return f"{self.id}.png"

    @dataclass
    class Nightmare(Unit):
        turn_counter: int = 0

        def start_turn(self):
            self.turn_counter += 1
            return self.turn_motion()

        # 적 모션 (start_turn에서 turn_counter가 증가한 뒤 호출됨)
        def turn_motion(self):
            return enemy_attack_nearby

        # 공격 및 스킬(자식 클래스에서 오버라이드)
        def basic_attack(self, player):
            damage = self.attack(player, self.atk)
            player.take_damage(damage)
            return ActionResult(target_hit=True, target_sound="attack4.mp3")

        def take_turn(self, player):
            return self.basic_attack(player)

    @dataclass
    class WilloWisp(Nightmare):
        id: str = "willowisp"
        name: str = _("도깨비불")
        max_mp: int = 50
        atk: int = 5
        defence: int = 5

        def turn_motion(self):
            if self.turn_counter % 2 == 1:
                return enemy_attack_nearby
            else:
                return enemy_attack_distance

        def take_turn(self, player):
            if self.turn_counter % 2 == 1:
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

        def turn_motion(self):
            if self.turn_counter % 3 == 0:
                return None
            else:
                return enemy_attack_distance

        def take_turn(self, player):
            if self.turn_counter % 3 == 1:
                return self.basic_attack(player)
            elif self.turn_counter % 3 == 2:
                player.take_sanity(10)
                return ActionResult(target_hit=True, target_sound="dark_magic.mp3")
            else:
                self.heal(self.atk)
                return ActionResult(self_effect="heal", self_sound="heal.mp3")

    @dataclass
    class Dreamwalker(Unit):
        # 여기서부터 미리 정의해두는
        sanity: int = 100
        crit_chance: int = 20
        crit_damage: float = 1.5
        dream_shard: int = 200 # 재화 (꿈의 파편)
        isInsane: bool = False

        # 노가다 방지용
        def __post_init__(self):
            super().__post_init__()
            # 스킬 슬롯 (자식 클래스의 __post_init__에서 채워 넣으세요)
            self.basic_skill = BasicAttack()
            self.skill_normal = None
            self.skill_chaos = None
            self.ultimate_normal = None
            self.ultimate_chaos = None
            self.special_normal = None
            self.special_chaos = None

        # 혼돈 버전 조건이 충족되면 그쪽을, 아니면 평상시 버전을 고름
        def _choose_skill(self, normal, chaos):
            if chaos is not None and chaos.is_visible(self):
                return chaos
            return normal

        def get_active_skill(self, slot):
            if slot == "attack":
                return self.basic_skill
            elif slot == "skill":
                return self._choose_skill(self.skill_normal, self.skill_chaos)
            elif slot == "ultimate":
                return self._choose_skill(self.ultimate_normal, self.ultimate_chaos)
            elif slot == "special_skill":
                return self._choose_skill(self.special_normal, self.special_chaos)
            raise ValueError(f"알 수 없는 스킬 슬롯: {slot}")

        def is_chaos_slot(self, slot):
            return isinstance(self.get_active_skill(slot), ChaoticSkill)

        def use_skill(self, slot, target=None):
            chosen = self.get_active_skill(slot)
            self.mp -= chosen.cost(self)
            return chosen.execute(self, target)

        # 유틸리티
        def take_sanity(self, amount):
            self.sanity = max(-100, self.sanity - amount)

        def recover_sanity(self, amount):
            self.sanity = min(100, self.sanity + amount)

        def sanity_roll(self):
            if self.sanity > 0 or abs(self.sanity) < random.randint(1, 100):
                self.isInsane = False
            else:
                self.isInsane = True

        def harm(self, amount):
            self.mp = max(1, self.mp - amount)

        # 이걸 따로 두는 이유는 축복 트리거로 작동할 예정이기 때문
        def suicide(self):
            self.mp = 0

        # 이미지 (기본적으로 캐릭터 id를 기반으로 파일명을 생성하며, 필요 시 자식 클래스에서 오버라이드)
        def image_standby(self):
            return f"{self.id}.png"

        def image_attack(self):
            return f"{self.id}_attack.png"

        def image_hit(self):
            return f"{self.id}_hit.png"

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

        def __post_init__(self):
            super().__post_init__()
            self.skill_normal = QuantumEntangle()
            self.skill_chaos = SelfHarm()
            self.ultimate_normal = QuantumExplosion()
            self.ultimate_chaos = HappySuicide()
            self.special_normal = Meditate()
            self.special_chaos = Headache()

