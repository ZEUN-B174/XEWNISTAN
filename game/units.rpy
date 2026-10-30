init 2 python:
    import copy
    import random
    from dataclasses import dataclass, field

    @dataclass
    class Player:
        level: int = 1
        exp: int = 0
        dream_crystal: int = 0 # 영구 재화 (꿈의 결정)
        run_count: int = 0
        story_progress: int = 0 # 심층 사건(메인 스토리) 해금 진행도

        def getEXP(self, dim, area):
            reached_steps = max(1, (dim - 1) * 8 + area)
            gained_exp = reached_steps * 30
            gained_crystal = reached_steps * 15
            self.exp += gained_exp
            self.dream_crystal += gained_crystal
            if self.exp >= 100:
                self.level += self.exp // 100
                self.exp %= 100
            return gained_exp, gained_crystal

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
        buffs: list = field(default_factory=list)

        def __post_init__(self):
            self.mp = self.max_mp

        # 버프/디버프가 반영된 실효 스탯 프로퍼티
        @property
        def eff_atk(self):
            flat = sum(b.atk_flat for b in self.buffs)
            pct = sum(b.atk_pct for b in self.buffs)
            return max(1, int((self.atk + flat) * max(0.1, 1.0 + pct)))

        @property
        def eff_defence(self):
            flat = sum(b.def_flat for b in self.buffs)
            pct = sum(b.def_pct for b in self.buffs)
            return max(0, int((self.defence + flat) * max(0.0, 1.0 + pct)))

        @property
        def eff_crit_chance(self):
            return max(0, self.crit_chance + sum(b.crit_chance_flat for b in self.buffs))

        @property
        def eff_crit_damage(self):
            return max(1.0, self.crit_damage + sum(b.crit_damage_flat for b in self.buffs))

        @property
        def dmg_taken_mult(self):
            return max(0.1, 1.0 + sum(b.dmg_taken_pct for b in self.buffs))

        def add_buff(self, effect):
            if effect is None:
                return
            new_fx = copy.copy(effect)
            for existing in self.buffs:
                if existing.id == new_fx.id:
                    existing.duration = max(existing.duration, new_fx.duration)
                    return
            self.buffs.append(new_fx)

        def tick_buffs(self):
            for b in self.buffs:
                if b.turn_mp > 0:
                    self.heal(b.turn_mp)
                elif b.turn_mp < 0:
                    self.take_damage(abs(b.turn_mp))
                if b.turn_sanity > 0 and hasattr(self, "recover_sanity"):
                    self.recover_sanity(b.turn_sanity)
                elif b.turn_sanity < 0 and hasattr(self, "take_sanity"):
                    self.take_sanity(abs(b.turn_sanity))
                b.duration -= 1
            self.buffs = [b for b in self.buffs if b.duration > 0]

        def clear_buffs(self):
            self.buffs.clear()

        def take_damage(self, amount):
            self.mp = max(0, self.mp - amount)

        def heal(self, amount):
            self.mp = min(self.max_mp, self.mp + amount)

        def attack(self, target, amount=None, coef=1.0):
            if amount is None:
                raw = self.eff_atk * coef
            else:
                atk_ratio = (self.eff_atk / self.atk) if self.atk > 0 else 1.0
                raw = amount * atk_ratio
            if self.eff_crit_chance > 0 and random.randint(1, 100) <= self.eff_crit_chance:
                raw = raw * self.eff_crit_damage
            mitigated = calc_damage(raw, target.eff_defence)
            return max(1, int(mitigated * target.dmg_taken_mult))

        def image(self):
            return f"{self.id}.png"

    @dataclass
    class Nightmare(Unit):
        turn_counter: int = 0

        def act_turn(self, player):
            self.turn_counter += 1
            return self.take_turn(player)

        # 적 기본 공격 헬퍼 (모션 + 타격 시점 데미지 적용을 ActionFx로 묶음)
        def basic_attack(self, player, coef=1.0, hits=1, motion=enemy_attack_nearby, sound="attack4.mp3", debuff=None):
            hit_callbacks = []
            for i in range(max(1, hits)):
                is_last = (i == max(1, hits) - 1)
                def _do_hit(last=is_last):
                    dmg = self.attack(player, coef=coef)
                    player.take_damage(dmg)
                    if last and debuff is not None:
                        player.add_buff(debuff)
                hit_callbacks.append(_do_hit)

            return ActionFx(
                motion=motion,
                target_hit=True,
                hits=max(1, hits),
                hit_interval=0.18 if hits > 1 else 0.25,
                target_sound=sound,
                hit_actions=hit_callbacks,
            )

        # 적 특수/마법 공격 헬퍼 (이성치 침식 + 정신력 피해 + 디버프)
        def magic_attack(self, player, dmg_coef=0.0, hits=1, sanity_dmg=0, debuff=None, motion=enemy_attack_distance, sound="dark_magic.mp3"):
            hit_callbacks = []
            for i in range(max(1, hits)):
                is_last = (i == max(1, hits) - 1)
                def _do_hit(last=is_last):
                    if dmg_coef > 0:
                        dmg = self.attack(player, coef=dmg_coef)
                        player.take_damage(dmg)
                    if last:
                        if sanity_dmg > 0:
                            player.take_sanity(sanity_dmg)
                        if debuff is not None:
                            player.add_buff(debuff)
                hit_callbacks.append(_do_hit)

            return ActionFx(
                motion=motion,
                target_hit=(dmg_coef > 0 or sanity_dmg > 0),
                hits=max(1, hits),
                hit_interval=0.18 if hits > 1 else 0.25,
                target_sound=sound,
                target_effect="debuff" if (debuff is not None and dmg_coef <= 0 and sanity_dmg <= 0) else None,
                hit_actions=hit_callbacks,
            )

        # 적 자가 회복/버프 헬퍼
        def heal_self(self, coef=1.0, buff=None, motion=None, sound="heal.mp3"):
            def _do_self():
                if coef > 0:
                    self.heal(int(self.eff_atk * coef))
                if buff is not None:
                    self.add_buff(buff)

            return ActionFx(
                motion=motion,
                self_effect="heal" if coef > 0 else "buff",
                self_sound=sound,
                self_action=_do_self,
            )

        def take_turn(self, player):
            return self.basic_attack(player)

        def scale(self, mult):
            self.max_mp = int(self.max_mp * mult)
            self.mp = self.max_mp
            self.atk = max(1, int(self.atk * mult))
            self.defence = max(1, int(self.defence * mult))
            return self

    @dataclass
    class WilloWisp(Nightmare):
        id: str = "willowisp"
        name: str = _("도깨비불")
        max_mp: int = 50
        atk: int = 5
        defence: int = 5

        def take_turn(self, player):
            if self.turn_counter % 2 == 1:
                return self.basic_attack(player)
            else:
                return self.magic_attack(player, sanity_dmg=5)

    @dataclass
    class Teruterubozu(Nightmare):
        id: str = "teruterubozu"
        name: str = _("테루테루보즈")
        max_mp: int = 30
        atk: int = 10
        defence: int = 5

        def take_turn(self, player):
            if self.turn_counter % 3 == 1:
                return self.basic_attack(player, motion=enemy_attack_distance)
            elif self.turn_counter % 3 == 2:
                return self.magic_attack(player, sanity_dmg=10)
            else:
                return self.heal_self(coef=1.0)

    @dataclass
    class AbyssWisp(WilloWisp):
        """정예 악몽: 심연의 도깨비불 (임시로 willowisp 이미지 사용)"""
        id: str = "willowisp"
        name: str = _("심연의 도깨비불 [정예]")
        max_mp: int = 90
        atk: int = 9
        defence: int = 10

        def take_turn(self, player):
            if self.turn_counter % 2 == 1:
                return self.basic_attack(player)
            else:
                return self.magic_attack(player, dmg_coef=0.7, sanity_dmg=12)

    @dataclass
    class CursedTeru(Teruterubozu):
        """정예 악몽: 저주받은 테루테루보즈 (임시로 teruterubozu 이미지 사용)"""
        id: str = "teruterubozu"
        name: str = _("목매단 테루테루보즈 [정예]")
        max_mp: int = 80
        atk: int = 12
        defence: int = 8

        def take_turn(self, player):
            if self.turn_counter % 3 == 1:
                return self.basic_attack(player, motion=enemy_attack_distance)
            elif self.turn_counter % 3 == 2:
                return self.magic_attack(player, sanity_dmg=15)
            else:
                return self.heal_self(coef=1.5)

    @dataclass
    class DreamBoss(Nightmare):
        """차원 보스 악몽 (차원별 이름/스탯 부여, 임시 이미지 사용)"""
        id: str = "teruterubozu"
        name: str = _("주인 악몽 [보스]")
        max_mp: int = 150
        atk: int = 14
        defence: int = 12

        def take_turn(self, player):
            if self.turn_counter % 3 == 0:
                # 3턴마다 강력한 정신 오염 + 피해
                return self.magic_attack(player, dmg_coef=1.5, sanity_dmg=15)
            else:
                return self.basic_attack(player)

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