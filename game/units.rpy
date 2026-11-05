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
        waves: list = field(default_factory=list)   # 보유 물결(축복) 리스트
        arcanas: list = field(default_factory=list) # 보유 아르카나(기물) 리스트
        guillotine_used: bool = False
        sedative_used: bool = False
        storm_crit_stack: float = 0.0
        _in_trigger: bool = False

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

        # ======================================================================
        # 물결(Wave) 및 아르카나(Arcana) 관리 헬퍼
        # ======================================================================
        def get_wave(self, wave_id):
            for w in self.waves:
                if w.id == wave_id:
                    return w
            return None

        def has_wave(self, wave_id):
            return self.get_wave(wave_id) is not None

        def count_wave_path(self, path):
            return sum(1 for w in self.waves if w.path == path)

        def has_synergy(self, path):
            return self.count_wave_path(path) >= 3

        def get_arcana(self, arcana_id):
            for a in self.arcanas:
                if a.id == arcana_id:
                    return a
            return None

        def has_arcana(self, arcana_id):
            return self.get_arcana(arcana_id) is not None

        def spend_shard(self, amount):
            self.dream_shard = max(0, self.dream_shard - amount)

        def add_wave(self, wave_obj):
            if wave_obj is None or self.has_wave(wave_obj.id):
                return
            new_w = copy.deepcopy(wave_obj)
            self.waves.append(new_w)
            if new_w.id == "sub_1_abyss_armor":
                bonus = 45 if new_w.upgraded else 25
                self.max_mp += bonus
                self.heal(bonus)

        def upgrade_wave(self, wave_id_or_obj):
            target_id = wave_id_or_obj.id if hasattr(wave_id_or_obj, "id") else wave_id_or_obj
            w = self.get_wave(target_id)
            if w is not None and not w.upgraded:
                w.upgraded = True
                if w.id == "sub_1_abyss_armor":
                    self.max_mp += 20
                    self.heal(20)
                return True
            return False

        def add_arcana(self, arcana_obj):
            if arcana_obj is None or self.has_arcana(arcana_obj.id):
                return
            new_a = copy.deepcopy(arcana_obj)
            self.arcanas.append(new_a)
            if new_a.id == "black_umbrella":
                self.defence += 6
            elif new_a.id == "golden_dreamcatcher":
                self.dream_shard += 80
            elif new_a.id == "eternal_ice":
                self.max_mp += 35
                self.heal(35)

        # ======================================================================
        # 물결 / 공명 / 아르카나가 반영된 실효 스탯 오버라이드
        # ======================================================================
        @property
        def eff_defence(self):
            flat = sum(b.def_flat for b in self.buffs)
            pct = sum(b.def_pct for b in self.buffs)
            w_calm = self.get_wave("cla_1_calm_surface")
            if w_calm is not None and self.sanity > 0:
                pct += 0.25 if w_calm.upgraded else 0.15
            w_armor = self.get_wave("sub_1_abyss_armor")
            if w_armor is not None:
                pct += 0.50 if w_armor.upgraded else 0.30
            if self.has_synergy("submerge"):
                pct += 0.25
            return max(0, int((self.defence + flat) * max(0.0, 1.0 + pct)))

        @property
        def eff_atk(self):
            flat = sum(b.atk_flat for b in self.buffs)
            w_trench = self.get_wave("sub_3_titan_trench")
            if w_trench is not None:
                flat += int(self.eff_defence * (0.80 if w_trench.upgraded else 0.50))

            pct = sum(b.atk_pct for b in self.buffs)
            lost_tens = int(((self.max_mp - self.mp) / max(1, self.max_mp)) * 10)
            w_back = self.get_wave("rup_1_backflow")
            if w_back is not None:
                pct += lost_tens * (0.07 if w_back.upgraded else 0.04)
            if self.has_synergy("rupture"):
                pct += lost_tens * 0.05

            w_calm = self.get_wave("cla_1_calm_surface")
            if w_calm is not None and self.sanity > 0:
                pct += 0.25 if w_calm.upgraded else 0.15

            if self.sanity <= 0:
                mad_tens = abs(self.sanity) // 10
                w_mad = self.get_wave("ero_1_mad_whisper")
                if w_mad is not None:
                    pct += mad_tens * (0.10 if w_mad.upgraded else 0.06)
                if self.has_synergy("erosion"):
                    pct += 0.25

            return max(1, int((self.atk + flat) * max(0.1, 1.0 + pct)))

        @property
        def eff_crit_chance(self):
            val = self.crit_chance + sum(b.crit_chance_flat for b in self.buffs)
            w_sharp = self.get_wave("tor_1_sharp_wave")
            if w_sharp is not None:
                val += 25 if w_sharp.upgraded else 15
            if self.has_synergy("torrent"):
                val += 15
            return max(0, val)

        @property
        def eff_crit_damage(self):
            val = self.crit_damage + sum(b.crit_damage_flat for b in self.buffs) + self.storm_crit_stack
            w_sharp = self.get_wave("tor_1_sharp_wave")
            if w_sharp is not None:
                val += 0.35 if w_sharp.upgraded else 0.20
            if self.has_synergy("torrent"):
                val += 0.30
            if self.has_arcana("bloodied_scalpel"):
                val += 0.35
            return round(max(1.0, val), 2)

        @property
        def dmg_taken_mult(self):
            mult = max(0.1, 1.0 + sum(b.dmg_taken_pct for b in self.buffs))
            w_ward = self.get_wave("sub_2_trench_ward")
            if w_ward is not None:
                mult *= (0.68 if w_ward.upgraded else 0.80)
            if self.has_synergy("clarity") and self.sanity > 0:
                mult *= 0.85
            return max(0.1, mult)

        @property
        def skill_cost_mult(self):
            mult = 1.0
            w_flow = self.get_wave("cla_2_lucid_flow")
            if w_flow is not None:
                mult *= (0.55 if w_flow.upgraded else 0.70)
            return mult

        # ======================================================================
        # 전투 액션 및 물결/아르카나 트리거
        # ======================================================================
        def attack(self, target, amount=None, coef=1.0):
            base_dmg = super().attack(target, amount=amount, coef=coef)
            mult = 1.0
            w_storm = self.get_wave("tor_3_abyss_storm")
            if w_storm is not None:
                mult *= (1.45 if w_storm.upgraded else 1.30)
            if target is not None and any(b.is_debuff for b in target.buffs):
                w_fear = self.get_wave("ero_2_fear_spread")
                if w_fear is not None:
                    mult *= (1.40 if w_fear.upgraded else 1.25)
                if self.has_synergy("erosion"):
                    mult *= 1.20
            return max(1, int(base_dmg * mult))

        def on_hit_target(self, target, dmg):
            if target is None:
                return
            w_storm = self.get_wave("tor_3_abyss_storm")
            if w_storm is not None:
                cap = 0.80 if w_storm.upgraded else 0.50
                step = 0.08 if w_storm.upgraded else 0.05
                self.storm_crit_stack = min(cap, round(self.storm_crit_stack + step, 2))

            if any(b.is_debuff for b in target.buffs):
                w_fear = self.get_wave("ero_2_fear_spread")
                if w_fear is not None:
                    self.heal(14 if w_fear.upgraded else 8)

            w_bubble = self.get_wave("ero_1_curse_bubble")
            if w_bubble is not None:
                target.add_buff(StatusEffect(
                    id="wave_erosion",
                    name=_("침식+") if w_bubble.upgraded else _("침식"),
                    duration=3 if w_bubble.upgraded else 2,
                    is_debuff=True,
                    def_pct=-0.35 if w_bubble.upgraded else -0.25,
                    turn_mp=-14 if w_bubble.upgraded else -8,
                ))

            w_splash = self.get_wave("tor_1_splash")
            if w_splash is not None and target.mp > 0:
                chance = 60 if w_splash.upgraded else 40
                if random.randint(1, 100) <= chance:
                    extra_dmg = max(1, int(self.eff_atk * (0.75 if w_splash.upgraded else 0.50)))
                    target.take_damage(extra_dmg)

        def on_battle_start(self, enemy_queue):
            self.clear_buffs()
            self.guillotine_used = False
            self.sedative_used = False
            self.storm_crit_stack = 0.0

            w_trench = self.get_wave("sub_3_titan_trench")
            if w_trench is not None:
                self.heal(int(self.max_mp * (0.25 if w_trench.upgraded else 0.15)))

            if self.has_arcana("broken_watch"):
                self.add_buff(StatusEffect(
                    id="arc_watch",
                    name=_("가속된 시간"),
                    duration=2,
                    atk_pct=0.35,
                    crit_chance_flat=25,
                ))

            if self.has_arcana("perwin_dongle") and enemy_queue:
                for e in enemy_queue:
                    e.add_buff(StatusEffect(
                        id="arc_dongle",
                        name=_("방화벽 해킹"),
                        duration=3,
                        is_debuff=True,
                        def_pct=-0.20,
                    ))

        def on_kill_enemy(self, enemy):
            w_foam = self.get_wave("tor_2_chain_foam")
            if w_foam is not None:
                self.heal(35 if w_foam.upgraded else 20)
                self.add_buff(StatusEffect(
                    id="wave_chain_foam",
                    name=_("연쇄 포말"),
                    duration=2,
                    atk_pct=0.50 if w_foam.upgraded else 0.30,
                ))

        def on_battle_win(self):
            w_flow = self.get_wave("cla_2_lucid_flow")
            if w_flow is not None:
                self.heal(25 if w_flow.upgraded else 15)
            if self.has_arcana("succubus_lipstick"):
                self.heal(10)

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
            if isinstance(chosen, ChaoticSkill):
                self._trigger_void_vortex(target)
            return chosen.execute(self, target)

        def _trigger_void_vortex(self, target=None):
            w_vortex = self.get_wave("ero_3_void_vortex")
            t = target if target is not None else (currentEnemy if on_battle else None)
            if w_vortex is not None and t is not None and t.mp > 0:
                dmg = max(1, int(self.eff_atk * (2.10 if w_vortex.upgraded else 1.40)))
                t.take_damage(dmg)
                t.add_buff(StatusEffect(
                    id="wave_vortex_vuln",
                    name=_("허수 침식"),
                    duration=2,
                    is_debuff=True,
                    dmg_taken_pct=0.40 if w_vortex.upgraded else 0.25,
                ))

        def _try_trigger_guillotine(self):
            w_guil = self.get_wave("rup_3_guillotine")
            if w_guil is not None and not self.guillotine_used:
                self.guillotine_used = True
                self.mp = max(1, int(self.max_mp * (0.80 if w_guil.upgraded else 0.50)))
                if on_battle and currentEnemy is not None and currentEnemy.mp > 0:
                    dmg = max(1, int(self.eff_atk * (6.50 if w_guil.upgraded else 4.50)))
                    currentEnemy.take_damage(dmg)
                return True
            return False

        # 유틸리티
        def take_damage(self, amount):
            self.mp = max(0, self.mp - amount)
            if on_battle and currentEnemy is not None and amount > 0:
                w_coral = self.get_wave("sub_1_thorn_coral")
                if w_coral is not None and currentEnemy.mp > 0:
                    reflect = max(1, int(self.eff_defence * (1.90 if w_coral.upgraded else 1.20)))
                    currentEnemy.take_damage(reflect)
                if self.has_synergy("submerge") and currentEnemy.mp > 0:
                    currentEnemy.take_damage(max(1, int(self.eff_defence * 0.80)))
                if self.has_arcana("eternal_ice") and currentEnemy.mp > 0:
                    currentEnemy.add_buff(StatusEffect(
                        id="arc_ice_chill",
                        name=_("만년빙 한기"),
                        duration=2,
                        is_debuff=True,
                        atk_pct=-0.20,
                    ))

            if 0 < self.mp <= int(self.max_mp * 0.30) and self.has_arcana("emergency_sedative") and not self.sedative_used:
                self.sedative_used = True
                self.heal(int(self.max_mp * 0.40))
                self.add_buff(StatusEffect(
                    id="arc_sedative",
                    name=_("응급 안정제"),
                    duration=2,
                    def_pct=0.40,
                ))

            if self.mp <= 0:
                self._try_trigger_guillotine()

        def heal(self, amount):
            super().heal(amount)
            w_mirror = self.get_wave("cla_3_mirror_light")
            if w_mirror is not None and not self._in_trigger and amount > 0:
                self._in_trigger = True
                self.recover_sanity(7 if w_mirror.upgraded else 4)
                if on_battle and currentEnemy is not None and currentEnemy.mp > 0:
                    dmg = max(1, int(amount * (1.40 if w_mirror.upgraded else 0.90)))
                    currentEnemy.take_damage(dmg)
                self._in_trigger = False

        def tick_buffs(self):
            super().tick_buffs()
            w_breath = self.get_wave("cla_1_deep_breath")
            if w_breath is not None:
                self.heal(max(1, int(self.max_mp * (0.10 if w_breath.upgraded else 0.06))))
                if w_breath.upgraded:
                    self.recover_sanity(2)
            if self.has_synergy("clarity") and self.sanity > 0:
                self.heal(6)

        def take_sanity(self, amount):
            w_ward = self.get_wave("sub_2_trench_ward")
            if on_battle and w_ward is not None:
                amount = max(1, int(amount * (0.50 if w_ward.upgraded else 0.65)))
            self.sanity = max(-100, self.sanity - amount)
            if amount > 0:
                self._trigger_void_vortex()

        def recover_sanity(self, amount):
            self.sanity = min(100, self.sanity + amount)

        def sanity_roll(self):
            if self.sanity > 0:
                self.isInsane = False
            else:
                chance = abs(self.sanity) + (35 if self.has_arcana("white_noise_tape") else 0)
                self.isInsane = (random.randint(1, 100) <= chance)

            if self.has_arcana("schrodinger_dice"):
                dice_buffs = [
                    StatusEffect(id="arc_dice", name=_("주사위: 맹공"), duration=1, atk_pct=0.25),
                    StatusEffect(id="arc_dice", name=_("주사위: 철벽"), duration=1, def_pct=0.30),
                    StatusEffect(id="arc_dice", name=_("주사위: 행운"), duration=1, crit_chance_flat=25),
                ]
                self.add_buff(random.choice(dice_buffs))

        def harm(self, amount):
            if self.has_synergy("rupture"):
                amount = max(1, int(amount * 0.80))
            self.mp = max(1, self.mp - amount)
            w_adr = self.get_wave("rup_1_adrenaline")
            if w_adr is not None:
                self.add_buff(StatusEffect(
                    id="wave_adrenaline",
                    name=_("붉은 잔물결"),
                    duration=2,
                    atk_pct=0.40 if w_adr.upgraded else 0.25,
                ))
            w_echo = self.get_wave("rup_2_crimson_echo")
            if w_echo is not None and on_battle and currentEnemy is not None and currentEnemy.mp > 0:
                dmg = max(1, int(self.eff_atk * (1.80 if w_echo.upgraded else 1.20)))
                currentEnemy.take_damage(dmg)
            if self.has_arcana("bloodied_scalpel"):
                self.dream_shard += 25

        # 이걸 따로 두는 이유는 축복 트리거로 작동할 예정이기 때문
        def suicide(self):
            self.mp = 0
            self._try_trigger_guillotine()

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