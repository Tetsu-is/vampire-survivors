import pyxel
import math
import random

# ゲーム画面サイズ
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 256

# 銃弾の速度
BULLET_SPEED = 4
BULLET_DAMAGE = 1

# 敵の速度
ENEMY_SPEED = 0.5
ENEMY_HP = 1
ENEMY_DAMAGE = 1
ENEMY_EXP = 1 # 敵がドロップする経験値

# ゲーム状態
GAME_STATE_PLAYING = 0
GAME_STATE_GAME_OVER = 1
GAME_STATE_LEVEL_UP = 2

# 敵の出現頻度 (フレーム数)
ENEMY_SPAWN_INTERVAL = 60

# 経験値オーブ
EXP_ORB_LIFETIME = 300 # 300フレーム(5秒)で消滅

# 衝突判定ヘルパー関数
def is_colliding(x1, y1, w1, h1, x2, y2, w2, h2):
    return x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2

# Ability Base Class
class Ability:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def apply_effect(self, player):
        # このメソッドは各アビリティでオーバーライドされるでやんす
        pass

# Specific Abilities
class MaxHpUp(Ability):
    def __init__(self):
        super().__init__("Max HP Up", "Increases player's max HP by 1.") # 英語に戻すでやんす

    def apply_effect(self, player):
        player.player_max_hp += 1
        player.player_hp += 1 # 最大HPが増えた分、現在HPも増やすでやんす

class MoveSpeedUp(Ability):
    def __init__(self):
        super().__init__("Move Speed Up", "Increases player's move speed slightly.") # 英語に戻すでやんす

    def apply_effect(self, player):
        player.player_speed += 0.5 # 仮で0.5増やすでやんす

class BulletSpeedUp(Ability):
    def __init__(self):
        super().__init__("Bullet Speed Up", "Increases bullet speed.") # 英語に戻すでやんす

    def apply_effect(self, player):
        player.bullet_bullet_speed_multiplier += 0.1 # 弾速を乗算で強化

class BulletDamageUp(Ability):
    def __init__(self):
        super().__init__("Bullet Damage Up", "Increases bullet damage.") # 英語にするでやんす

    def apply_effect(self, player):
        player.bullet_damage += 1

# 全てのアビリティのリスト
ALL_ABILITIES = [
    MaxHpUp(),
    MoveSpeedUp(),
    BulletSpeedUp(),
    BulletDamageUp(),
]

class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.dx = BULLET_SPEED * math.cos(math.radians(angle))
        self.dy = BULLET_SPEED * math.sin(math.radians(angle))
        self.is_active = True
        self.width = 2
        self.height = 2

    def update(self):
        if not self.is_active: return
        self.x += self.dx
        self.y += self.dy
        if not (0 <= self.x < SCREEN_WIDTH and 0 <= self.y < SCREEN_HEIGHT):
            self.is_active = False

    def draw(self):
        if self.is_active: pyxel.rect(self.x, self.y, self.width, self.height, 8)

class Enemy:
    def __init__(self, player_x, player_y):
        side = random.randint(0, 3)
        if side == 0: self.x, self.y = random.randint(0, SCREEN_WIDTH - 8), -8
        elif side == 1: self.x, self.y = SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT - 8)
        elif side == 2: self.x, self.y = random.randint(0, SCREEN_WIDTH - 8), SCREEN_HEIGHT
        else: self.x, self.y = -8, random.randint(0, SCREEN_HEIGHT - 8)

        self.hp = ENEMY_HP
        self.speed = ENEMY_SPEED
        self.is_active = True
        self.width = 8
        self.height = 8

    def update(self, player_x, player_y):
        if not self.is_active: return
        angle = math.atan2(player_y - self.y, player_x - self.x)
        self.x += self.speed * math.cos(angle)
        self.y += self.speed * math.sin(angle)

    def draw(self):
        if self.is_active: pyxel.rect(self.x, self.y, self.width, self.height, 1)

class ExperienceOrb:
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value
        self.life = EXP_ORB_LIFETIME
        self.is_active = True
        self.width = 4
        self.height = 4

    def update(self):
        if not self.is_active: return
        self.life -= 1
        if self.life <= 0:
            self.is_active = False

    def draw(self):
        if self.is_active: pyxel.rect(self.x, self.y, self.width, self.height, 11) # 11は黄色

class App:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Vampire Survivors-like")
        
        self.reset_game_state()
        
        pyxel.mouse(False) 
        pyxel.run(self.update, self.draw)

    def level_up(self):
        self.player_level += 1
        self.player_exp -= self.exp_to_next_level
        self.exp_to_next_level = int(self.exp_to_next_level * 1.5) # 次のレベルに必要な経験値を1.5倍にするでやんす
        self.player_hp = self.player_max_hp # HPを全回復するでやんす

        # アビリティをランダムに3つ選択
        self.selected_abilities_for_level_up = random.sample(ALL_ABILITIES, 3)
        self.current_ability_selection_index = 0 # 選択中のアビリティのインデックス

        self.game_state = GAME_STATE_LEVEL_UP # ゲーム状態をレベルアップ選択に切り替えるでやんす

    def reset_game_state(self):
        self.player_x = SCREEN_WIDTH / 2
        self.player_y = SCREEN_HEIGHT / 2
        self.player_width = 8
        self.player_height = 8
        self.player_max_hp = 3
        self.player_hp = self.player_max_hp
        self.player_level = 1
        self.player_exp = 0
        self.exp_to_next_level = 5 # 次のレベルアップに必要な経験値
        self.player_speed = 1.0 # プレイヤーの移動速度の初期値

        self.bullet_damage = BULLET_DAMAGE # 弾のダメージ
        self.bullet_bullet_speed_multiplier = 1.0 # 弾速の倍率

        self.bullets = []
        self.enemies = []
        self.exp_orbs = [] # 経験値オーブを管理するリストでやんす
        self.enemy_spawn_timer = 0
        self.invincible_timer = 0 # 無敵時間タイマー
        self.is_invincible = False # 無敵状態フラグ

        self.game_state = GAME_STATE_PLAYING # ゲーム状態
        self.final_time = 0 # 最終的な生存時間
        self.selected_abilities_for_level_up = [] # レベルアップ時に選択されるアビリティのリスト
        self.current_ability_selection_index = 0 # レベルアップ時の選択カーソル位置

    def update(self):
        if self.game_state == GAME_STATE_PLAYING:
            # プレイヤーの移動処理
            if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A): self.player_x -= self.player_speed
            if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D): self.player_x += self.player_speed
            if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W): self.player_y -= self.player_speed
            if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S): self.player_y += self.player_speed
            self.player_x = max(0, min(self.player_x, SCREEN_WIDTH - self.player_width))
            self.player_y = max(0, min(self.player_y, SCREEN_HEIGHT - self.player_height))

            # スペースキーで銃弾発射
            if pyxel.btnp(pyxel.KEY_SPACE):
                angle = math.degrees(math.atan2(pyxel.mouse_y - self.player_y, pyxel.mouse_x - self.player_x))
                self.bullets.append(Bullet(self.player_x + self.player_width / 2, self.player_y + self.player_height / 2, angle))

            for bullet in self.bullets: bullet.update()
            for enemy in self.enemies: enemy.update(self.player_x, self.player_y)
            for orb in self.exp_orbs: orb.update()

            # 敵の出現ロジック
            self.enemy_spawn_timer += 1
            if self.enemy_spawn_timer >= ENEMY_SPAWN_INTERVAL:
                self.enemies.append(Enemy(self.player_x, self.player_y))
                self.enemy_spawn_timer = 0

            # --- 衝突判定とダメージ処理 ---
            # 銃弾と敵の衝突判定
            for bullet in self.bullets:
                if not bullet.is_active: continue
                for enemy in self.enemies:
                    if not enemy.is_active: continue
                    if is_colliding(bullet.x, bullet.y, bullet.width, bullet.height, enemy.x, enemy.y, enemy.width, enemy.height):
                        bullet.is_active = False
                        enemy.hp -= BULLET_DAMAGE
                        if enemy.hp <= 0:
                            enemy.is_active = False
                            self.exp_orbs.append(ExperienceOrb(enemy.x, enemy.y, ENEMY_EXP)) # 経験値オーブをドロップ
                        break

            # プレイヤーと敵の衝突判定
            if not self.is_invincible:
                for enemy in self.enemies:
                    if not enemy.is_active: continue
                    if is_colliding(self.player_x, self.player_y, self.player_width, self.player_height, enemy.x, enemy.y, enemy.width, enemy.height):
                        self.player_hp -= ENEMY_DAMAGE
                        if self.player_hp <= 0:
                            self.game_state = GAME_STATE_GAME_OVER
                            self.final_time = pyxel.frame_count
                            print("Game Over!") # デバッグ用
                        else:
                            self.is_invincible = True
                            self.invincible_timer = 90 # 3秒間の無敵 (30fps * 3s)
                        break # 1フレームに1回だけダメージを受ける

            # 無敵時間処理
            if self.is_invincible:
                self.invincible_timer -= 1
                if self.invincible_timer <= 0:
                    self.is_invincible = False

            # プレイヤーと経験値オーブの衝突判定
            for orb in self.exp_orbs:
                if not orb.is_active: continue
                if is_colliding(self.player_x, self.player_y, self.player_width, self.player_height, orb.x, orb.y, orb.width, orb.height):
                    self.player_exp += orb.value
                    orb.is_active = False
                    if self.player_exp >= self.exp_to_next_level:
                        self.level_up()

            # 非アクティブなオブジェクトの削除
            self.bullets = [b for b in self.bullets if b.is_active]
            self.enemies = [e for e in self.enemies if e.is_active]
            self.exp_orbs = [o for o in self.exp_orbs if o.is_active]
        
        elif self.game_state == GAME_STATE_GAME_OVER:
            if pyxel.btnp(pyxel.KEY_R): # Rキーでリトライ
                self.reset_game_state() # ゲームを初期化
            if pyxel.btnp(pyxel.KEY_Q): # Qキーで終了
                pyxel.quit()
        
        elif self.game_state == GAME_STATE_LEVEL_UP:
            if pyxel.btnp(pyxel.KEY_UP): # 上キーで選択肢を上に移動
                self.current_ability_selection_index = (self.current_ability_selection_index - 1) % len(self.selected_abilities_for_level_up)
            if pyxel.btnp(pyxel.KEY_DOWN): # 下キーで選択肢を下に移動
                self.current_ability_selection_index = (self.current_ability_selection_index + 1) % len(self.selected_abilities_for_level_up)
            
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_Z): # スペースキーまたはZキーで決定
                chosen_ability = self.selected_abilities_for_level_up[self.current_ability_selection_index]
                chosen_ability.apply_effect(self) # 選択されたアビリティの効果をプレイヤーに適用
                
                self.selected_abilities_for_level_up = [] # 選択肢をクリア
                self.current_ability_selection_index = 0 # 選択カーソルをリセット
                self.game_state = GAME_STATE_PLAYING # ゲーム状態をプレイ中に戻す

    def draw(self):
        pyxel.cls(0)
    
        if self.game_state == GAME_STATE_PLAYING:
            for orb in self.exp_orbs: orb.draw()
            for bullet in self.bullets: bullet.draw()
            for enemy in self.enemies: enemy.draw()
            
            # プレイヤーの描画 (無敵時間中は点滅)
            if self.is_invincible:
                if (pyxel.frame_count // 15) % 2 == 0: # 0.5秒間隔で点滅 (30fpsで15フレーム)
                        pyxel.rect(self.player_x, self.player_y, self.player_width, self.player_height, 7)
            else:
                pyxel.rect(self.player_x, self.player_y, self.player_width, self.player_height, 7)
            
            # 照準
            x, y = pyxel.mouse_x, pyxel.mouse_y
            pyxel.pset(x, y, 7)
            pyxel.line(x - 5, y, x - 1, y, 7); pyxel.line(x + 1, y, x + 5, y, 7)
            pyxel.line(x, y - 5, x, y - 1, 7); pyxel.line(x, y + 1, x, y + 5, 7)
            
            # UI
            pyxel.text(5, 5, f"HP: {self.player_hp}/{self.player_max_hp}", 7)
            pyxel.text(5, 15, f"LV: {self.player_level}", 7)
            # 経験値バー
            pyxel.rect(5, 25, 100, 5, 13) # 背景
            exp_bar_width = 100 * self.player_exp / self.exp_to_next_level
            pyxel.rect(5, 25, exp_bar_width, 5, 11) # 経験値

            # 経過時間表示 (MM:SS)
            total_seconds = pyxel.frame_count // 30 # Pyxelはデフォルトで30fps
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
            pyxel.text(message_x, message_y, game_over_message, 8) # 赤色
    
            final_total_seconds = self.final_time // 30
            final_minutes = final_total_seconds // 60
            final_seconds = final_total_seconds % 60
            final_time_str = f"SURVIVED: {final_minutes:02}:{final_seconds:02}"
            final_time_x = (SCREEN_WIDTH - len(final_time_str) * pyxel.FONT_WIDTH) // 2
            pyxel.text(final_time_x, message_y + pyxel.FONT_HEIGHT * 2, final_time_str, 7)
    
            retry_x = (SCREEN_WIDTH - len(retry_message) * pyxel.FONT_WIDTH) // 2
            pyxel.text(retry_x, message_y + pyxel.FONT_HEIGHT * 4, retry_message, 7)
    
            quit_x = (SCREEN_WIDTH - len(quit_message) * pyxel.FONT_WIDTH) // 2
            pyxel.text(quit_x, message_y + pyxel.FONT_HEIGHT * 5, quit_message, 7)
        
        elif self.game_state == GAME_STATE_LEVEL_UP:
            pyxel.rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0) # 画面を黒く塗りつぶすでやんす

            title_text = "LEVEL UP!"
            # タイトルは中央より少し左に寄せるでやんす（後で微調整可能）
            pyxel.text(SCREEN_WIDTH // 2 - len(title_text) * pyxel.FONT_WIDTH / 2, 30, title_text, 7)

            start_y = 60
            for i, ability in enumerate(self.selected_abilities_for_level_up):
                display_text = f"{ability.name}: {ability.description}"
                text_color = 7 # 白
                
                display_x = SCREEN_WIDTH // 2 - 80 # 固定位置に表示するでやんす

                if i == self.current_ability_selection_index:
                    text_color = 3 # 緑
                    pyxel.text(display_x - 10, start_y + i * 20, ">", text_color) # カーソル
                
                pyxel.text(display_x, start_y + i * 20, display_text, text_color)

            confirm_text = "Press SPACE/Z to select"
            # 確認メッセージも中央より少し左に寄せるでやんす
            pyxel.text(SCREEN_WIDTH // 2 - len(confirm_text) * pyxel.FONT_WIDTH / 2, SCREEN_HEIGHT - 30, confirm_text, 7)
if __name__ == "__main__":
    App()
