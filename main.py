import math
import random
import sys # sysモジュールをインポート

import pyxel

# ゲーム画面サイズ
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 256

# 銃弾の速度
BULLET_SPEED = 4
BULLET_DAMAGE = 20

# 敵の速度
ENEMY_SPEED = 0.5
ENEMY_HP = 50
ENEMY_DAMAGE = 1
ENEMY_EXP = 1  # 敵がドロップする経験値

# ゲーム状態
GAME_STATE_PLAYING = 0
GAME_STATE_GAME_OVER = 1
GAME_STATE_LEVEL_UP = 2

# 敵の出現頻度 (フレーム数)
ENEMY_SPAWN_INTERVAL = 60

# 経験値オーブ
EXP_ORB_LIFETIME = 300  # 300フレーム(5秒)で消滅
BIG_EXP_ORB_CHANCE = 0.1 # 多めにドロップする経験値オーブの出現確率 (10%)
BIG_EXP_ORB_MULTIPLIER = 5 # 多めにドロップする経験値オーブの倍率 (5倍)
NORMAL_EXP_ORB_COLOR = 11 # 通常の経験値オーブの色 (黄色)
BIG_EXP_ORB_COLOR = 10 # 多めにドロップする経験値オーブの色 (緑色)


# 衝突判定ヘルパー関数
def is_colliding(x1, y1, w1, h1, x2, y2, w2, h2):
    return x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2


# Ability Base Class
class Ability:
    def __init__(self, name, description, max_level=-1): # max_levelを追加 (デフォルトは無限)
        self.name = name
        self.description = description
        self.max_level = max_level # このアビリティが取得できる最大レベル

    def apply_effect(self, player):
        # このメソッドは各アビリティでオーバーライドされるでやんす
        pass


# Specific Abilities
class MaxHpUp(Ability):
    def __init__(self):
        super().__init__(
            "Max HP Up", "Increases player's max HP by 1."
        )  # 英語に戻すでやんす

    def apply_effect(self, player):
        player.player_max_hp += 1
        player.player_hp += 1  # 最大HPが増えた分、現在HPも増やすでやんす


class MoveSpeedUp(Ability):
    def __init__(self):
        super().__init__(
            "Move Speed Up", "Increases player's move speed slightly."
        )  # 英語に戻すでやんす

    def apply_effect(self, player):
        player.player_speed += 0.5  # 仮で0.5増やすでやんす


class BulletSpeedUp(Ability):
    def __init__(self):
        super().__init__(
            "Bullet Speed Up", "Increases bullet speed."
        )  # 英語に戻すでやんす

    def apply_effect(self, player):
        player.bullet_bullet_speed_multiplier += 0.1  # 弾速を乗算で強化


class BulletDamageUp(Ability):
    def __init__(self):
        super().__init__(
            "Bullet Damage Up", "Increases bullet damage."
        )  # 英語にするでやんす

    def apply_effect(self, player):
        player.bullet_damage += 1


class AutoAimBulletAbility(Ability):
    def __init__(self):
        super().__init__(
            "Auto-aim Bullet", "Periodically fires a homing bullet.", max_level=1 # max_levelを1に設定
        )

    def apply_effect(self, player):
        player.has_auto_aim_bullet = True
        # アビリティ取得時にタイマー間隔などを設定することもできる
        # player.auto_aim_bullet_interval = 120 # 例えば2秒ごと

class PiercingShotAbility(Ability):
    def __init__(self):
        super().__init__(
            "Piercing Shot", "Bullets pierce through enemies and deal damage."
        )

    def apply_effect(self, player):
        player.has_piercing_shot = True
        player.pierce_level += 1 # 貫通レベルを上げるでやんす (最初は1、次は2と増える)

class SummonGhostAbility(Ability):
    def __init__(self):
        super().__init__(
            "Summon Ghost", "Summons a ghost that fights for you.", max_level=1 # max_levelを1に設定
        )

    def apply_effect(self, player):
        player.has_ghost_summon = True
        # 最初のゴーストを召喚 (player_x, player_yはプレイヤーの初期位置、BULLET_DAMAGEは現在の弾丸ダメージ)
        player.ghosts.append(Ghost(player.player_x, player.player_y, player.bullet_damage))

class BulletFireRateUp(Ability):
    def __init__(self):
        super().__init__(
            "Bullet Fire Rate Up", "Increases bullet fire rate."
        )

    def apply_effect(self, player):
        player.player_fire_rate_multiplier += 0.1 # 発射レートを上げる (0.1は仮の値)


# 全てのアビリティのリスト
ALL_ABILITIES = [
    MaxHpUp(),
    MoveSpeedUp(),
    BulletSpeedUp(),
    BulletDamageUp(),
    AutoAimBulletAbility(),
    PiercingShotAbility(),
    SummonGhostAbility(), # 新しいアビリティを追加
    BulletFireRateUp(), # 新しいアビリティを追加
]


class Bullet:
    def __init__(self, x, y, angle, pierce_level=0): # pierce_levelを追加
        self.x = x
        self.y = y
        self.angle = angle
        self.dx = BULLET_SPEED * math.cos(math.radians(angle))
        self.dy = BULLET_SPEED * math.sin(math.radians(angle))
        self.is_active = True
        self.width = 2
        self.height = 2
        self.life_time = 90  # 3秒で消えるでやんす (30fps * 3s)
        self.pierce_level = pierce_level # 貫通レベル (0で貫通なし、1以上で貫通)
        self.pierced_count = 0 # 実際に貫通した敵の数
        self.hit_enemies = set() # 既にヒットした敵のIDを記録 (二重ヒット防止)

    def get_damage(self):
        # 貫通回数に応じてダメージを減衰させるでやんす
        # 例えば、貫通1回ごとにダメージが20%減少する (調整可能)
        decay_rate = 0.2
        # ダメージが0を下回らないようにするでやんす
        return max(0, BULLET_DAMAGE * (1 - self.pierced_count * decay_rate))

    def update(self):
        if not self.is_active:
            return
        self.x += self.dx
        self.y += self.dy
        self.life_time -= 1
        if self.life_time <= 0:
            self.is_active = False
        if not (0 <= self.x < SCREEN_WIDTH and 0 <= self.y < SCREEN_HEIGHT):
            self.is_active = False

    def draw(self):
        if self.is_active:
            pyxel.rect(self.x, self.y, self.width, self.height, 8)


class HomingBullet(Bullet):
    def __init__(self, x, y, target_enemy, angle, pierce_level=0, homing_strength=0.05, homing_delay=30): # pierce_levelを追加
        # 親クラスのコンストラクタを呼び出す
        super().__init__(x, y, angle, pierce_level) # pierce_levelも渡すでやんす！
        self.speed = BULLET_SPEED * 0.8  # 通常弾より少し遅くする
        self.target = target_enemy
        self.homing_strength = homing_strength
        self.width = 3  # 見分けがつくように少し大きくする
        self.height = 3
        self.life_time = 90  # 3秒で消えるでやんす (30fps * 3s)
        self.homing_delay = homing_delay # 追尾開始までの猶予フレーム

    def update(self, enemies):
        if not self.is_active:
            return

        self.life_time -= 1
        if self.life_time <= 0:
            self.is_active = False

        if self.homing_delay > 0:
            self.homing_delay -= 1
            # 猶予期間中は直進するでやんす（dx, dyは初期の方向を保持している）
        else:
            # ターゲットが存在し、かつアクティブか確認
            if self.target and self.target.is_active:
                # ターゲットへの角度を計算
                target_angle = math.atan2(self.target.y - self.y, self.target.x - self.x)
                current_angle = math.atan2(self.dy, self.dx)

                # 角度の差を正規化
                angle_diff = target_angle - current_angle
                while angle_diff > math.pi:
                    angle_diff -= 2 * math.pi
                while angle_diff < -math.pi:
                    angle_diff += 2 * math.pi

                # homing_strengthに基づいて角度を徐々に変える
                new_angle = current_angle + angle_diff * self.homing_strength
                self.dx = self.speed * math.cos(new_angle)
                self.dy = self.speed * math.sin(new_angle)
            # else の処理は既にコメントアウトして直進するように変更済み
        # ターゲットを失ったら直進するでやんす。速度はそのまま維持。
        # self.dx, self.dy はターゲット追尾中の最後の速度ベクトルを保持しているため、
        # これをそのまま利用すればよいでやんす。

        self.x += self.dx
        self.y += self.dy
        if not (0 <= self.x < SCREEN_WIDTH and 0 <= self.y < SCREEN_HEIGHT):
            self.is_active = False

    def find_closest_enemy(self, enemies):
        closest_enemy = None
        min_dist = float('inf')
        for enemy in enemies:
            if enemy.is_active:
                dist = math.hypot(self.x - enemy.x, self.y - enemy.y)
                if dist < min_dist:
                    min_dist = dist
                    closest_enemy = enemy
        return closest_enemy

    def draw(self):
        if self.is_active:
            # 追尾弾は色を変える（例：シアン）
            pyxel.rect(self.x, self.y, self.width, self.height, 12)


class Enemy:
    def __init__(self, player_x, player_y, phase=1):  # phase引数を追加
        side = random.randint(0, 3)
        if side == 0:
            self.x, self.y = random.randint(0, SCREEN_WIDTH - 8), -8
        elif side == 1:
            self.x, self.y = SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT - 8)
        elif side == 2:
            self.x, self.y = random.randint(0, SCREEN_WIDTH - 8), SCREEN_HEIGHT
        else:
            self.x, self.y = -8, random.randint(0, SCREEN_HEIGHT - 8)

        # フェーズに応じてステータスを決定
        self.hp = int(ENEMY_HP * (1 + (phase - 1) * 0.5)) # フェーズごとに50%ずつHPを増加
        self.speed = ENEMY_SPEED * (1 + (phase - 1) * 0.1) # フェーズごとに10%ずつスピードを増加
        self.is_active = True
        
        # フェーズに応じて大きさと色を変える
        size_multiplier = 1 + (phase - 1) * 0.2
        self.width = int(8 * size_multiplier)
        self.height = int(8 * size_multiplier)
        self.color = 1 + ((phase - 1) % 14) # pyxelのカラーパレットに合わせて色をサイクルさせる (0は黒なので1から)
        self.phase = phase

    def update(self, player_x, player_y):
        if not self.is_active:
            return
        angle = math.atan2(player_y - self.y, player_x - self.x)
        self.x += self.speed * math.cos(angle)
        self.y += self.speed * math.sin(angle)

    def draw(self):
        if self.is_active:
            pyxel.rect(self.x, self.y, self.width, self.height, self.color)

# ゴーストの攻撃レート (フレーム数)
GHOST_ATTACK_INTERVAL = 30 # 1秒間に1回攻撃 (30FPS)
GHOST_ATTACK_RANGE = 30 # ゴーストの攻撃範囲
GHOST_ATTACK_EFFECT_DURATION = 5 # ゴーストが攻撃時に色が変わるフレーム数

class Ghost:
    def __init__(self, player_x, player_y, initial_player_bullet_damage):
        self.x = player_x
        self.y = player_y
        self.width = 6 # サイズを小さくする
        self.height = 6 # サイズを小さくする
        self.original_color = 7 # 白色
        self.attack_color = 8 # 赤色 (攻撃時に変わる色)
        self.color = self.original_color
        self.is_active = True
        self.target_offset_x = random.uniform(-20, 20) # プレイヤーの周りをふわふわするためのオフセット
        self.target_offset_y = random.uniform(-20, 20)
        self.speed = 0.8 # プレイヤー追従速度
        
        self.base_attack_damage = initial_player_bullet_damage * 2.0 # プレイヤー弾丸ダメージの200% (2倍)
        self.current_attack_damage = self.base_attack_damage
        self.attack_timer = 0
        self.attack_interval = GHOST_ATTACK_INTERVAL
        self.attack_effect_timer = 0 # 攻撃エフェクト用タイマー


    def update(self, player_x, player_y, player_level, enemies):
        if not self.is_active:
            return

        # プレイヤーレベルに応じて攻撃力強化
        # プレイヤーレベルが1上がるごとに1.1倍に強化される
        self.current_attack_damage = self.base_attack_damage * (1.1 ** (player_level - 1))


        # プレイヤーの周りを追従
        target_x = player_x + self.target_offset_x
        target_y = player_y + self.target_offset_y
        
        angle = math.atan2(target_y - self.y, target_x - self.x)
        self.x += self.speed * math.cos(angle)
        self.y += self.speed * math.sin(angle)

        # 攻撃エフェクトタイマーの更新
        if self.attack_effect_timer > 0:
            self.attack_effect_timer -= 1
            if self.attack_effect_timer == 0:
                self.color = self.original_color # エフェクト終了で元の色に戻す

        # 攻撃ロジック
        self.attack_timer += 1
        if self.attack_timer >= self.attack_interval:
            self.attack_timer = 0
            
            # 攻撃範囲内の最も近い敵を探す
            closest_enemy = None
            min_dist = GHOST_ATTACK_RANGE
            for enemy in enemies:
                if enemy.is_active:
                    dist = math.hypot(self.x - enemy.x, self.y - enemy.y)
                    if dist < min_dist:
                        min_dist = dist
                        closest_enemy = enemy
            
            if closest_enemy:
                # 敵にダメージを与える
                closest_enemy.hp -= self.current_attack_damage
                # 攻撃エフェクトを開始
                self.color = self.attack_color
                self.attack_effect_timer = GHOST_ATTACK_EFFECT_DURATION
                # 敵が倒れたかどうかのチェックと経験値オーブの生成はAppクラス側で行うでやんす
                # Appクラスのupdateメソッドで、全ての敵のhpをチェックして、0以下ならexp_orbを生成する
                # という処理を入れれば良いでやんす。

    def draw(self):
        if self.is_active:
            # 今回は単純に白い四角で表現するでやんす
            pyxel.rect(self.x, self.y, self.width, self.height, self.color)


class ExperienceOrb:
    def __init__(self, x, y, value, color=NORMAL_EXP_ORB_COLOR): # color引数を追加
        self.x = x
        self.y = y
        self.value = value
        self.life = EXP_ORB_LIFETIME
        self.is_active = True
        self.width = 4
        self.height = 4
        self.color = color # 色を保持するでやんす

    def update(self):
        if not self.is_active:
            return
        self.life -= 1
        if self.life <= 0:
            self.is_active = False

    def draw(self):
        if self.is_active:
            pyxel.rect(self.x, self.y, self.width, self.height, self.color)  # 指定された色で描画


class App:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Vampire Survivors-like")

        self.debug_abilities = []
        if len(sys.argv) > 1:
            # コマンドライン引数からデバッグ用アビリティを取得
            # 例: uv run main.py --piercing_shot --summon_ghost
            for arg in sys.argv[1:]:
                if arg.startswith('--'):
                    self.debug_abilities.append(arg[2:].replace('_', ' ').title())


        self.reset_game_state()

        pyxel.mouse(False)
        pyxel.run(self.update, self.draw)

    def level_up(self):
        self.player_level += 1
        self.player_exp -= self.exp_to_next_level
        self.exp_to_next_level = int(
            self.exp_to_next_level * 1.5
        )  # 次のレベルに必要な経験値を1.5倍にするでやんす
        self.player_hp = self.player_max_hp  # HPを全回復するでやんす

        # 取得可能なアビリティのリストを作成
        available_abilities = []
        for ability in ALL_ABILITIES:
            # 現在のレベルを取得 (なければ0)
            current_level = self.acquired_ability_levels.get(ability.name, 0)
            # max_levelが-1 (無限) またはまだmax_levelに達していない場合のみ追加
            if ability.max_level == -1 or current_level < ability.max_level:
                available_abilities.append(ability)

        # 選択可能なアビリティが3つ未満の場合、可能な限り選択するでやんす
        num_choices = min(3, len(available_abilities))
        self.selected_abilities_for_level_up = random.sample(available_abilities, num_choices)
        self.current_ability_selection_index = 0  # 選択中のアビリティのインデックス

        self.game_state = (
            GAME_STATE_LEVEL_UP  # ゲーム状態をレベルアップ選択に切り替えるでやんす
        )

    def reset_game_state(self):
        self.player_x = SCREEN_WIDTH / 2
        self.player_y = SCREEN_HEIGHT / 2
        self.player_width = 8
        self.player_height = 8
        self.player_max_hp = 3
        self.player_hp = self.player_max_hp
        self.player_level = 1
        self.player_exp = 0
        self.exp_to_next_level = 5  # 次のレベルアップに必要な経験値
        self.player_speed = 1.0  # プレイヤーの移動速度の初期値

        self.bullet_damage = BULLET_DAMAGE  # 弾のダメージ
        self.bullet_bullet_speed_multiplier = 1.0  # 弾速の倍率

        self.bullets = []
        self.enemies = []
        self.exp_orbs = []  # 経験値オーブを管理するリストでやんす
        self.enemy_spawn_timer = 0
        self.invincible_timer = 0  # 無敵時間タイマー
        self.is_invincible = False  # 無敵状態フラグ

        self.game_state = GAME_STATE_PLAYING
        self.final_time = 0
        self.selected_abilities_for_level_up = []
        self.current_ability_selection_index = 0
        self.has_auto_aim_bullet = False
        self.shot_cooldown_frames = 10  # 1秒間に3発 (30FPSなので 30 / 3 = 10フレーム)
        self.last_shot_frame = -10  # 最初の発射をすぐできるように初期値を設定
        self.player_fire_rate_multiplier = 1.0 # 発射レートの乗数
        self.current_phase = 1  # 現在のゲームフェーズ
        self.has_piercing_shot = False # 貫通弾アビリティを持っているか
        self.pierce_level = 0 # 貫通レベル (貫通できる敵の数 + 1)
        self.acquired_ability_levels = {} # 取得済みアビリティのレベルを記録する辞書
        self.has_ghost_summon = False # ゴースト召喚アビリティを持っているか
        self.ghosts = [] # 召喚されたゴーストオブジェクトを保持するリスト

        # 移動しっぱなしモード関連
        self.is_continuous_move_mode_on = False # 移動しっぱなしモードのオン/オフ
        self.continuous_move_dx = 0 # 移動しっぱなしモード時のX方向移動量
        self.continuous_move_dy = 0 # 移動しっぱなしモード時のY方向移動量

        # デバッグ用アビリティの適用
        for debug_ability_name in self.debug_abilities:
            for ability in ALL_ABILITIES:
                if ability.name == debug_ability_name:
                    ability.apply_effect(self)
                    # 取得済みアビリティレベルを更新
                    self.acquired_ability_levels[ability.name] = \
                        self.acquired_ability_levels.get(ability.name, 0) + 1
                    break




    def find_closest_enemy_for_player(self):
        closest_enemy = None
        min_dist = float('inf')
        for enemy in self.enemies:
            if enemy.is_active:
                dist = math.hypot(self.player_x - enemy.x, self.player_y - enemy.y)
                if dist < min_dist:
                    min_dist = dist
                    closest_enemy = enemy
        return closest_enemy

    def update(self):
        if self.game_state == GAME_STATE_PLAYING:
            # LShiftキーで移動しっぱなしモードをトグル
            if pyxel.btnp(pyxel.KEY_LSHIFT):
                self.is_continuous_move_mode_on = not self.is_continuous_move_mode_on
                # モードがオフになったら、継続移動を停止
                if not self.is_continuous_move_mode_on:
                    self.continuous_move_dx = 0
                    self.continuous_move_dy = 0

            # プレイヤーの移動処理
            if self.is_continuous_move_mode_on:
                # 継続移動モードがオンの場合
                input_dx = 0
                input_dy = 0
                if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
                    input_dx -= 1
                if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
                    input_dx += 1
                if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W):
                    input_dy -= 1
                if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S):
                    input_dy += 1

                # 新しい方向入力があれば、継続移動の方向を更新
                if input_dx != 0 or input_dy != 0:
                    self.continuous_move_dx = input_dx
                    self.continuous_move_dy = input_dy
                
                # 継続移動を実行
                self.player_x += self.continuous_move_dx * self.player_speed
                self.player_y += self.continuous_move_dy * self.player_speed

            else:
                # 継続移動モードがオフの場合（通常の移動）
                if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
                    self.player_x -= self.player_speed
                if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
                    self.player_x += self.player_speed
                if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W):
                    self.player_y -= self.player_speed
                if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S):
                    self.player_y += self.player_speed

            self.player_x = max(0, min(self.player_x, SCREEN_WIDTH - self.player_width))
            self.player_y = max(
                0, min(self.player_y, SCREEN_HEIGHT - self.player_height)
            )
            
            # 移動しっぱなしモードで壁に到達したら停止する
            if self.is_continuous_move_mode_on:
                if self.player_x <= 0 or self.player_x >= SCREEN_WIDTH - self.player_width:
                    self.continuous_move_dx = 0
                if self.player_y <= 0 or self.player_y >= SCREEN_HEIGHT - self.player_height:
                    self.continuous_move_dy = 0

            # スペースキーで銃弾発射
            if pyxel.btn(pyxel.KEY_SPACE) and pyxel.frame_count >= self.last_shot_frame + (self.shot_cooldown_frames / self.player_fire_rate_multiplier):
                self.last_shot_frame = pyxel.frame_count # 発射時刻を更新
                if self.has_auto_aim_bullet:
                    # 自動追尾弾アビリティがある場合、HomingBulletを発射
                    closest_enemy = self.find_closest_enemy_for_player()
                    if closest_enemy:
                        # プレイヤーからマウスカーソルへの角度を計算
                        angle = math.degrees(
                            math.atan2(
                                pyxel.mouse_y - self.player_y, pyxel.mouse_x - self.player_x
                            )
                        )
                        self.bullets.append(
                            HomingBullet(
                                self.player_x + self.player_width / 2,
                                self.player_y + self.player_height / 2,
                                closest_enemy,
                                angle,
                                self.pierce_level, # pierce_levelを渡すでやんす！
                            )
                        )
                else:
                    # 通常の弾丸を発射
                    angle = math.degrees(
                        math.atan2(
                            pyxel.mouse_y - self.player_y, pyxel.mouse_x - self.player_x
                        )
                    )
                    self.bullets.append(
                        Bullet(
                            self.player_x + self.player_width / 2,
                            self.player_y + self.player_height / 2,
                            angle,
                            self.pierce_level, # pierce_levelを渡すでやんす！
                        )
                    )
            for bullet in self.bullets:
                if isinstance(bullet, HomingBullet):
                    bullet.update(self.enemies)
                else:
                    bullet.update()
            for enemy in self.enemies:
                enemy.update(self.player_x, self.player_y)
            for orb in self.exp_orbs:
                orb.update()
            for ghost in self.ghosts: # ゴーストの更新
                ghost.update(self.player_x, self.player_y, self.player_level, self.enemies)

            # ゲーム時間に応じてフェーズを更新
            if pyxel.frame_count > 0 and pyxel.frame_count % 1800 == 0: # 1分 (30FPS * 60秒 = 1800フレーム) ごとにフェーズ更新
                self.current_phase += 1
                # print(f"Phase changed to: {self.current_phase}") # デバッグ用

            # 敵の出現ロジック
            self.enemy_spawn_timer += 1
            if self.enemy_spawn_timer >= ENEMY_SPAWN_INTERVAL:
                # 現在のフェーズを渡して敵を生成
                self.enemies.append(Enemy(self.player_x, self.player_y, self.current_phase))
                self.enemy_spawn_timer = 0

            # --- 衝突判定とダメージ処理 ---
            # 銃弾と敵の衝突判定
            for bullet in self.bullets:
                if not bullet.is_active:
                    continue
                for enemy in self.enemies:
                    if not enemy.is_active:
                        continue
                    # 既にこの弾丸でヒット済みの敵は無視するでやんす (貫通弾の二重ヒット防止)
                    if enemy in bullet.hit_enemies:
                        continue

                    if is_colliding(
                        bullet.x,
                        bullet.y,
                        bullet.width,
                        bullet.height,
                        enemy.x,
                        enemy.y,
                        enemy.width,
                        enemy.height,
                    ):
                        # 弾丸がヒットした敵を記録するでやんす
                        bullet.hit_enemies.add(enemy)
                        
                        # ダメージ計算はBulletクラスのget_damageメソッドを使うでやんす
                        damage_to_deal = bullet.get_damage()
                        enemy.hp -= damage_to_deal
                        
                        if enemy.hp <= 0:
                            enemy.is_active = False
                            # 経験値オーブの生成ロジックを変更
                            exp_value = ENEMY_EXP * enemy.phase
                            exp_color = NORMAL_EXP_ORB_COLOR
                            if random.random() < BIG_EXP_ORB_CHANCE: # BIG_EXP_ORB_CHANCEの確率で
                                exp_value *= BIG_EXP_ORB_MULTIPLIER
                                exp_color = BIG_EXP_ORB_COLOR
                            self.exp_orbs.append(
                                ExperienceOrb(enemy.x, enemy.y, exp_value, exp_color)
                            )  # 経験値オーブをドロップ (色も渡す)
                        
                        # 貫通弾の場合の処理
                        if bullet.pierce_level > 0:
                            bullet.pierced_count += 1
                            if bullet.pierced_count > bullet.pierce_level:
                                bullet.is_active = False # 貫通回数を超えたら弾を非アクティブにする
                        else:
                            bullet.is_active = False # 貫通能力がなければ1体ヒットで非アクティブ

            # ここで全ての敵のHPをチェックし、倒れた敵を処理するでやんす
            # 銃弾、ゴーストどちらの攻撃でもここを通るようにするでやんす
            for enemy in self.enemies:
                if enemy.is_active and enemy.hp <= 0:
                    enemy.is_active = False
                    # 経験値オーブの生成ロジックを変更
                    exp_value = ENEMY_EXP * enemy.phase
                    exp_color = NORMAL_EXP_ORB_COLOR
                    if random.random() < BIG_EXP_ORB_CHANCE: # BIG_EXP_ORB_CHANCEの確率で
                        exp_value *= BIG_EXP_ORB_MULTIPLIER
                        exp_color = BIG_EXP_ORB_COLOR
                    self.exp_orbs.append(
                        ExperienceOrb(enemy.x, enemy.y, exp_value, exp_color)
                    )  # 経験値オーブをドロップ (色も渡す)

            # プレイヤーと敵の衝突判定
            if not self.is_invincible:
                for enemy in self.enemies:
                    if not enemy.is_active:
                        continue
                    if is_colliding(
                        self.player_x,
                        self.player_y,
                        self.player_width,
                        self.player_height,
                        enemy.x,
                        enemy.y,
                        enemy.width,
                        enemy.height,
                    ):
                        self.player_hp -= ENEMY_DAMAGE
                        if self.player_hp <= 0:
                            self.game_state = GAME_STATE_GAME_OVER
                            self.final_time = pyxel.frame_count
                            print("Game Over!")  # デバッグ用
                        else:
                            self.is_invincible = True
                            self.invincible_timer = 90  # 3秒間の無敵 (30fps * 3s)
                        break  # 1フレームに1回だけダメージを受ける

            # 無敵時間処理
            if self.is_invincible:
                self.invincible_timer -= 1
                if self.invincible_timer <= 0:
                    self.is_invincible = False

            # プレイヤーと経験値オーブの衝突判定
            for orb in self.exp_orbs:
                if not orb.is_active:
                    continue
                if is_colliding(
                    self.player_x,
                    self.player_y,
                    self.player_width,
                    self.player_height,
                    orb.x,
                    orb.y,
                    orb.width,
                    orb.height,
                ):
                    self.player_exp += orb.value
                    orb.is_active = False
                    if self.player_exp >= self.exp_to_next_level:
                        self.level_up()

            # 非アクティブなオブジェクトの削除
            self.bullets = [b for b in self.bullets if b.is_active]
            self.enemies = [e for e in self.enemies if e.is_active]
            self.exp_orbs = [o for o in self.exp_orbs if o.is_active]

        elif self.game_state == GAME_STATE_GAME_OVER:
            if pyxel.btnp(pyxel.KEY_R):  # Rキーでリトライ
                self.reset_game_state()  # ゲームを初期化
            if pyxel.btnp(pyxel.KEY_Q):  # Qキーで終了
                pyxel.quit()

        elif self.game_state == GAME_STATE_LEVEL_UP:
            if pyxel.btnp(pyxel.KEY_UP):  # 上キーで選択肢を上に移動
                self.current_ability_selection_index = (
                    self.current_ability_selection_index - 1
                ) % len(self.selected_abilities_for_level_up)
            if pyxel.btnp(pyxel.KEY_DOWN):  # 下キーで選択肢を下に移動
                self.current_ability_selection_index = (
                    self.current_ability_selection_index + 1
                ) % len(self.selected_abilities_for_level_up)

            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(
                pyxel.KEY_Z
            ):  # エンターキーまたはZキーで決定
                chosen_ability = self.selected_abilities_for_level_up[
                    self.current_ability_selection_index
                ]
                chosen_ability.apply_effect(
                    self
                )  # 選択されたアビリティの効果をプレイヤーに適用

                # 取得したアビリティのレベルを更新するでやんす
                self.acquired_ability_levels[chosen_ability.name] = \
                    self.acquired_ability_levels.get(chosen_ability.name, 0) + 1

                self.selected_abilities_for_level_up = []  # 選択肢をクリア
                self.current_ability_selection_index = 0  # 選択カーソルをリセット
                self.game_state = GAME_STATE_PLAYING  # ゲーム状態をプレイ中に戻す

    def draw(self):
        pyxel.cls(0)

        if self.game_state == GAME_STATE_PLAYING:
            for orb in self.exp_orbs:
                orb.draw()
            for bullet in self.bullets:
                bullet.draw()
            for enemy in self.enemies:
                enemy.draw()
            for ghost in self.ghosts: # ゴーストの描画
                ghost.draw()

            # プレイヤーの描画 (無敵時間中は点滅)
            if self.is_invincible:
                if (
                    pyxel.frame_count // 15
                ) % 2 == 0:  # 0.5秒間隔で点滅 (30fpsで15フレーム)
                    pyxel.rect(
                        self.player_x,
                        self.player_y,
                        self.player_width,
                        self.player_height,
                        7,
                    )
            else:
                pyxel.rect(
                    self.player_x,
                    self.player_y,
                    self.player_width,
                    self.player_height,
                    7,
                )

            # 照準
            x, y = pyxel.mouse_x, pyxel.mouse_y
            pyxel.pset(x, y, 7)
            pyxel.line(x - 5, y, x - 1, y, 7)
            pyxel.line(x + 1, y, x + 5, y, 7)
            pyxel.line(x, y - 5, x, y - 1, 7)
            pyxel.line(x, y + 1, x, y + 5, 7)

            # UI
            pyxel.text(5, 5, f"HP: {self.player_hp}/{self.player_max_hp}", 7)
            pyxel.text(5, 15, f"LV: {self.player_level}", 7)
            # 経験値バー
            pyxel.rect(5, 25, 100, 5, 13)  # 背景
            exp_bar_width = 100 * self.player_exp / self.exp_to_next_level
            pyxel.rect(5, 25, exp_bar_width, 5, 11)  # 経験値

            # 経過時間表示 (MM:SS)
            total_seconds = pyxel.frame_count // 30  # Pyxelはデフォルトで30fps
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            time_str = f"TIME: {minutes:02}:{seconds:02}"
            pyxel.text(5, 35, time_str, 7)

        elif self.game_state == GAME_STATE_GAME_OVER:
            game_over_message = "GAME OVER"
            retry_message = "Press 'R' to Retry"
            quit_message = "Press 'Q' to Quit"

            message_x = (SCREEN_WIDTH - len(game_over_message) * pyxel.FONT_WIDTH) // 2
            message_y = SCREEN_HEIGHT // 2 - pyxel.FONT_HEIGHT * 2
            pyxel.text(message_x, message_y, game_over_message, 8)  # 赤色

            final_total_seconds = self.final_time // 30
            final_minutes = final_total_seconds // 60
            final_seconds = final_total_seconds % 60
            final_time_str = f"SURVIVED: {final_minutes:02}:{final_seconds:02}"
            final_time_x = (SCREEN_WIDTH - len(final_time_str) * pyxel.FONT_WIDTH) // 2
            pyxel.text(
                final_time_x, message_y + pyxel.FONT_HEIGHT * 2, final_time_str, 7
            )

            retry_x = (SCREEN_WIDTH - len(retry_message) * pyxel.FONT_WIDTH) // 2
            pyxel.text(retry_x, message_y + pyxel.FONT_HEIGHT * 4, retry_message, 7)

            quit_x = (SCREEN_WIDTH - len(quit_message) * pyxel.FONT_WIDTH) // 2
            pyxel.text(quit_x, message_y + pyxel.FONT_HEIGHT * 5, quit_message, 7)

        elif self.game_state == GAME_STATE_LEVEL_UP:
            pyxel.rect(
                0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0
            )  # 画面を黒く塗りつぶすでやんす

            title_text = "LEVEL UP!"
            # タイトルは中央より少し左に寄せるでやんす（後で微調整可能）
            pyxel.text(
                SCREEN_WIDTH // 2 - len(title_text) * pyxel.FONT_WIDTH / 2,
                30,
                title_text,
                7,
            )

            start_y = 60
            for i, ability in enumerate(self.selected_abilities_for_level_up):
                display_text = f"{ability.name}: {ability.description}"
                text_color = 7  # 白

                display_x = SCREEN_WIDTH // 2 - 80  # 固定位置に表示するでやんす

                if i == self.current_ability_selection_index:
                    text_color = 3  # 緑
                    pyxel.text(
                        display_x - 10, start_y + i * 20, ">", text_color
                    )  # カーソル

                pyxel.text(display_x, start_y + i * 20, display_text, text_color)

            confirm_text = "Press ENTER/Z to select"
            # 確認メッセージも中央より少し左に寄せるでやんす
            pyxel.text(
                SCREEN_WIDTH // 2 - len(confirm_text) * pyxel.FONT_WIDTH / 2,
                SCREEN_HEIGHT - 30,
                confirm_text,
                7,
            )


if __name__ == "__main__":
    App()
