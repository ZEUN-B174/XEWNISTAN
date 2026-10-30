init 1 python:
    import copy
    import random
    from dataclasses import dataclass, field

    # 방어력에 따른 데미지 감쇄 상수. 이 값만큼 방어력이 있으면 피해량이 절반이 됨.
    DEFENCE_CONSTANT = 50

    def calc_damage(amount, target_defence):
        eff_def = max(0, target_defence)
        return int(amount * (DEFENCE_CONSTANT / (DEFENCE_CONSTANT + eff_def)))

    @dataclass
    class StatusEffect:
        """
        버프 / 디버프(상태이상) 데이터 클래스.
        Unit.buffs에 등록되며 턴 종료 시 지속시간(duration)이 감소함.
        """
        id: str
        name: str
        duration: int = 2               # 지속 턴 수
        is_debuff: bool = False         # True면 디버프(붉은색), False면 버프(보라/푸른색)
        atk_pct: float = 0.0            # 공격력 증감 비율 (예: 0.3 = +30%, -0.2 = -20%)
        atk_flat: int = 0               # 공격력 고정 증감
        def_pct: float = 0.0            # 방어력 증감 비율
        def_flat: int = 0               # 방어력 고정 증감
        crit_chance_flat: int = 0       # 치명타 확률 고정 증감 (%)
        crit_damage_flat: float = 0.0   # 치명타 피해 배율 고정 증감
        dmg_taken_pct: float = 0.0      # 받는 피해 증감 비율 (예: 0.25 = 받는 피해 +25%, -0.3 = 30% 경감)
        turn_mp: int = 0                # 매 턴 종료 시 정신력 변화 (+회복 / -피해)
        turn_sanity: int = 0            # 매 턴 종료 시 이성치 변화 (+회복 / -침식)

    @dataclass
    class ActionFx:
        """
        공격/스킬/턴 처리 결과로 리턴하는 연출 및 타격 시퀀스 객체.
        battle 루프는 이 값만 보고 연출(이동 모션/다단히트/사운드/버프)을 결정하기 때문에,
        새 스킬을 추가할 때 battle 루프를 건드릴 필요가 없어짐.
        """
        motion: object = None               # 시전 시 캐릭터 이동 모션 (None이면 제자리)
        target_hit: bool = False            # 상대(적 또는 플레이어)에게 피격 연출을 보여줄지
        hits: int = 1                       # 타격 횟수 (다단히트 시 2 이상)
        hit_interval: float = 0.25          # 타격 간 대기 시간(초)
        target_sound: str = "attack5.mp3"
        target_effect: str = None           # None / "debuff" — 피격 외에 상대에게 일어나는 연출
        self_effect: str = None             # None / "heal" / "harm" / "buff" / "debuff" — 시전자 본인에게 일어나는 연출
        self_sound: str = None
        self_action: object = None          # 시전자 연출 타이밍에 실행할 콜백 (선택)
        hit_actions: list = field(default_factory=list) # 각 타격 타이밍마다 실행할 콜백 리스트

        def total_hits(self):
            if self.hit_actions:
                return len(self.hit_actions)
            if self.target_hit:
                return max(1, self.hits)
            return 0

        def apply_hit(self, idx):
            if 0 <= idx < len(self.hit_actions) and callable(self.hit_actions[idx]):
                self.hit_actions[idx]()

    @dataclass
    class Skill:
        name: str = ""
        desc: str = ""          # 스킬 설명
        cost_coef: float = 0.0  # 공격력 기반으로 산정됨 (다른 스탯 쓰면 그 스탯 기준)
        motion: object = None   # 시전 시 캐릭터 이동 모션 (None이면 제자리)

        # 선언형(데이터 기반) 스킬용 기본 속성 — 특수 기믹 스킬은 execute()를 오버라이드
        dmg_coef: float = 0.0               # 타당 공격력 계수
        hits: int = 1                       # 타격 횟수 (다단히트 시 2 이상)
        heal_coef: float = 0.0              # 시전자 공격력 대비 정신력 회복 계수
        harm_coef: float = 0.0              # 시전자 공격력 대비 자해 계수
        sanity_change: int = 0              # 시전자 이성치 변화량 (+회복 / -감소)
        target_sanity_dmg: int = 0          # 상대 이성치 피해량
        self_buff: StatusEffect = None      # 시전자에게 부여할 버프/디버프
        target_debuff: StatusEffect = None  # 상대에게 부여할 디버프
        target_sound: str = "attack5.mp3"
        self_sound: str = None

        # 타격(단타/다단히트/디버프) ActionFx 생성 헬퍼
        def hit_fx(self, user, target, dmg_coef=None, hits=None, motion=..., sound=None, debuff=None, sanity_dmg=0):
            use_coef = self.dmg_coef if dmg_coef is None else dmg_coef
            use_hits = self.hits if hits is None else hits
            use_motion = self.motion if motion is ... else motion
            use_sound = self.target_sound if sound is None else sound
            use_debuff = self.target_debuff if debuff is None else debuff
            use_sanity_dmg = self.target_sanity_dmg if sanity_dmg == 0 else sanity_dmg

            hit_callbacks = []
            for i in range(max(1, use_hits)):
                is_last = (i == max(1, use_hits) - 1)
                def _do_hit(last=is_last):
                    if use_coef > 0 and target is not None:
                        dmg = user.attack(target, coef=use_coef)
                        target.take_damage(dmg)
                    if last and target is not None:
                        if use_sanity_dmg > 0 and hasattr(target, "take_sanity"):
                            target.take_sanity(use_sanity_dmg)
                        if use_debuff is not None:
                            target.add_buff(use_debuff)
                hit_callbacks.append(_do_hit)

            return ActionFx(
                motion=use_motion,
                target_hit=(use_coef > 0 or use_sanity_dmg > 0),
                hits=max(1, use_hits),
                hit_interval=0.18 if use_hits > 1 else 0.25,
                target_sound=use_sound,
                target_effect="debuff" if (use_debuff is not None and use_coef <= 0) else None,
                hit_actions=hit_callbacks,
            )

        # 시전자 본인 연출(회복/자해/버프) ActionFx 생성 헬퍼
        def self_fx(self, effect="heal", sound=None, motion=None, action=None):
            return ActionFx(
                motion=motion,
                self_effect=effect,
                self_sound=sound if sound is not None else self.self_sound,
                self_action=action,
            )

        # 기본 실행 로직 (특수 기믹 스킬은 자식 클래스에서 오버라이드)
        def execute(self, user, target):
            fx = ActionFx(
                motion=self.motion,
                target_sound=self.target_sound,
                self_sound=self.self_sound,
            )

            # 1. 시전자 본인 효과 (자해 / 회복 / 이성치 변화 / 자신 버프)
            has_self_work = (
                self.harm_coef > 0
                or self.heal_coef > 0
                or self.sanity_change != 0
                or self.self_buff is not None
            )
            if has_self_work:
                if self.harm_coef > 0:
                    fx.self_effect = "harm"
                elif self.heal_coef > 0 or self.sanity_change > 0:
                    fx.self_effect = "heal"
                elif self.self_buff is not None:
                    fx.self_effect = "debuff" if self.self_buff.is_debuff else "buff"
                elif self.sanity_change < 0:
                    fx.self_effect = "harm"

                def _apply_self():
                    if self.harm_coef > 0:
                        user.harm(int(user.eff_atk * self.harm_coef))
                    if self.heal_coef > 0:
                        user.heal(int(user.eff_atk * self.heal_coef))
                    if self.sanity_change > 0 and hasattr(user, "recover_sanity"):
                        user.recover_sanity(self.sanity_change)
                    elif self.sanity_change < 0 and hasattr(user, "take_sanity"):
                        user.take_sanity(abs(self.sanity_change))
                    if self.self_buff is not None:
                        user.add_buff(self.self_buff)

                fx.self_action = _apply_self

            # 2. 대상 타격(단타/다단히트) 및 디버프 효과
            if self.dmg_coef > 0 or self.target_sanity_dmg > 0 or self.target_debuff is not None:
                hit_fx_obj = self.hit_fx(user, target)
                fx.target_hit = hit_fx_obj.target_hit
                fx.hits = hit_fx_obj.hits
                fx.hit_interval = hit_fx_obj.hit_interval
                fx.target_effect = hit_fx_obj.target_effect
                fx.hit_actions = hit_fx_obj.hit_actions

            return fx

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
        cost_coef: float = 0.0
        dmg_coef: float = 1.0
        motion: object = attack_nearby

    ## 테스터 스킬

    # 양자 얽힘 (일반 스킬)
    @dataclass
    class QuantumEntangle(Skill):
        name: str = "양자 얽힘"
        desc: str = "공격력 200%의 피해를 가한다."
        cost_coef: float = 0.5
        dmg_coef: float = 2.0
        motion: object = attack_distance

    # self.harm() (일반 스킬 - 혼돈)
    @dataclass
    class SelfHarm(ChaoticSkill):
        name: str = "self.harm()"
        desc: str = "[자해]를 한다. 현재 이성치에 따라 정신력 소모량과 이성치 회복량이 달라지며, 반비례의 관계를 가진다."
        cost_coef: float = 0.0
        motion: object = None

        def execute(self, user, target):
            user.harm(user.max_mp // 2)
            user.recover_sanity(abs(user.sanity) // 2)
            return self.self_fx("harm", sound="harm.mp3")

        def is_visible(self, user):
            return user.isInsane

    # 명상 (특수 스킬)
    @dataclass
    class Meditate(Skill):
        name: str = "명상"
        desc: str = "공격력의 100%만큼 정신력을 회복하고 이성치를 5 회복한다."
        cost_coef: float = 0.0
        heal_coef: float = 1.0
        sanity_change: int = 5
        self_sound: str = "heal.mp3"

    # ??■?■■ (특수 스킬 - 혼돈)
    @dataclass
    class Headache(ChaoticSkill):
        name: str = "??■?■■"
        desc: str = "현재 이성치에 따라 공격력의 150%만큼 정신력이 회복하거나 감소한다 이성치는 10 회복되거나 줄어든다."
        cost_coef: float = 0.0
        motion: object = None

        def execute(self, user, target):
            dice = random.randint(1, 100)
            if dice > abs(user.sanity):
                user.heal(int(user.eff_atk * 1.5))
                user.recover_sanity(10)
                return self.self_fx("heal", sound="heal.mp3")
            else:
                user.harm(int(user.eff_atk * 1.5))
                user.take_sanity(10)
                return self.self_fx("harm", sound="harm.mp3")

        def is_visible(self, user):
            return user.sanity <= 0

    # 양자 폭발 (궁극기)
    @dataclass
    class QuantumExplosion(Skill):
        name: str = "양자 폭발"
        desc: str = "공격력 400%의 피해를 가한다."
        cost_coef: float = 2.0
        dmg_coef: float = 4.0
        motion: object = attack_distance

    # 행■한자■ (궁극기 - 혼돈)
    @dataclass
    class HappySuicide(ChaoticSkill):
        name: str = "행■한자■"
        desc: str = "[자살] 시도를 한다. 현재 이성치에 따라 성공 확률이 달라지며. 실패 시에는 이성치를 소모해 피해를 가한다."
        cost_coef: float = 0.0
        motion: object = attack_delayed_nearby

        def execute(self, user, target):
            dice = random.randint(1, 100)
            madness = abs(user.sanity)
            if dice > madness:
                user.take_sanity(5 + int(madness * 0.2))
                coef = 4.0 + 4.0 * madness * 0.01
                return self.hit_fx(user, target, dmg_coef=coef)
            else:
                user.suicide() # 1972년 11월 21일 플레이어는 오렌지병이었던 자1살로 사2망해
                return self.self_fx("harm", motion=None)

        def is_visible(self, user):
            return user.isInsane