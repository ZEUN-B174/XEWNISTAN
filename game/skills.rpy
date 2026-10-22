init 1 python:
    import random
    from dataclasses import dataclass

    # 방어력에 따른 데미지 감쇄 상수. 이 값만큼 방어력이 있으면 피해량이 절반이 됨.
    DEFENCE_CONSTANT = 50

    def calc_damage(amount, target_defence):
        return int(amount * (DEFENCE_CONSTANT / (DEFENCE_CONSTANT + target_defence)))

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
    class Skill:
        name: str
        desc: str # 스킬 설명
        cost_coef: float # 공격력 기반으로 산정됨 (다른 스탯 쓰면 그 스탯 기준)
        motion: object = None # 시전 시 캐릭터 이동 모션 (None이면 제자리)

        # 나중에 오버라이드 하세요
        def execute(self, user, target):
            return ActionResult()

        def cost(self, user):
            return int(user.atk * self.cost_coef)

        def is_available(self, user):
            return user.mp > self.cost(user)

        def is_visible(self, user):
            return True

    @dataclass
    class ChaoticSkill(Skill):
        def is_visible(self, user):
            return False

    ### 스킬 목록

    ## 범용 스킬

    # 일반 공격(공격력)
    @dataclass
    class BasicAttack(Skill):
        name: str = "일반 공격"
        desc: str = "공격력 100%의 피해를 가한다."
        cost_coef: float = 0
        motion: object = attack_nearby

        def execute(self, user, target):
            damage = user.attack(target, user.atk)
            target.take_damage(damage)
            return ActionResult(target_hit=True)

    ## 테스터 스킬

    # 양자 얽힘 (일반 스킬)
    @dataclass
    class QuantumEntangle(Skill):
        name: str = "양자 얽힘"
        desc: str = "공격력 200%의 피해를 가한다."
        cost_coef: float = 0.5
        motion: object = attack_distance

        def execute(self, user, target):
            damage = user.attack(target, user.atk * 2)
            target.take_damage(damage)
            return ActionResult(target_hit=True)

    # self.harm() (일반 스킬 - 혼돈)
    @dataclass
    class SelfHarm(ChaoticSkill):
        name: str = "self.harm()"
        desc: str = "[자해]를 한다. 현재 이성치에 따라 정신력 소모량과 이성치 회복량이 달라지며, 반비례의 관계를 가진다."
        cost_coef: float = 0
        motion: object = None

        def execute(self, user, target):
            user.harm(user.max_mp // 2)
            user.recover_sanity(abs(user.sanity) // 2)
            return ActionResult(self_effect="harm", self_sound="harm.mp3")

        def is_visible(self, user):
            return user.isInsane

    # 명상 (특수 스킬)
    @dataclass
    class Meditate(Skill):
        name: str = "명상"
        desc: str = "공격력의 100%만큼 정신력을 회복하고 이성치를 5 회복한다."
        cost_coef: float = 0
        motion: object = None

        def execute(self, user, target):
            user.heal(int(user.atk))
            user.recover_sanity(5)
            return ActionResult(self_effect="heal", self_sound="heal.mp3")

    # ??■?■■ (특수 스킬 - 혼돈)
    @dataclass
    class Headache(ChaoticSkill):
        name: str = "??■?■■"
        desc: str = "현재 이성치에 따라 공격력의 150%만큼 정신력이 회복하거나 감소한다 이성치는 10 회복되거나 줄어든다."
        cost_coef: float = 0
        motion: object = None

        def execute(self, user, target):
            dice = random.randint(1, 100)
            if dice > abs(user.sanity):
                user.heal(int(user.atk * 1.5))
                user.recover_sanity(10)
                return ActionResult(self_effect="heal", self_sound="heal.mp3")
            else:
                user.harm(int(user.atk * 1.5))
                user.take_sanity(10)
                return ActionResult(self_effect="harm", self_sound="harm.mp3")

        def is_visible(self, user):
            return user.sanity <= 0

    # 양자 폭발 (궁극기)
    @dataclass
    class QuantumExplosion(Skill):
        name: str = "양자 폭발"
        desc: str = "공격력 400%의 피해를 가한다."
        cost_coef: float = 2.0
        motion: object = attack_distance

        def execute(self, user, target):
            damage = user.attack(target, user.atk * 4)
            target.take_damage(damage)
            return ActionResult(target_hit=True)

    # 행■한자■ (궁극기 - 혼돈)
    @dataclass
    class HappySuicide(ChaoticSkill):
        name: str = "행■한자■"
        desc: str = "[자살] 시도를 한다. 현재 이성치에 따라 성공 확률이 달라지며. 실패 시에는 이성치를 소모해 피해를 가한다."
        cost_coef: float = 0
        motion: object = attack_delayed_nearby

        def execute(self, user, target):
            dice = random.randint(1, 100)
            madness = abs(user.sanity)
            if dice > madness:
                user.take_sanity(5 + int(madness * 0.2))
                damage = user.attack(target, user.atk * (4 + 4 * madness * 0.01))
                target.take_damage(damage)
                return ActionResult(target_hit=True)
            else:
                user.suicide() # 1972년 11월 21일 플레이어는 오렌지병이었던 자1살로 사2망해
                return ActionResult(self_effect="harm")

        def is_visible(self, user):
            return user.isInsane

