from flask import Flask, render_template, request, redirect, url_for
import cv2
import numpy as np

app = Flask(__name__)

class BaseballGame:
    def __init__(self):
        self.inning = 1
        self.outs = 0
        self.score = {"Home": 0, "Guest": 0}
        self.bases = [False, False, False]  # First, Second, Third
        self.current_team = "Guest"

    def detect_dice(self, image_path):
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 11, 2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        dice_values = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 1000 < area < 10000:
                mask = np.zeros(gray.shape, np.uint8)
                cv2.drawContours(mask, [contour], 0, 255, -1)
                die = cv2.bitwise_and(gray, gray, mask=mask)
                pips = cv2.countNonZero(cv2.inRange(die, 200, 255))
                if pips < 50:
                    dice_values.append(1)
                elif pips < 100:
                    dice_values.append(2)
                elif pips < 150:
                    dice_values.append(3)
                elif pips < 200:
                    dice_values.append(4)
                elif pips < 250:
                    dice_values.append(5)
                else:
                    dice_values.append(6)
        return dice_values

    def capture_and_process_dice(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            cv2.imshow('Press Space to Capture Dice Roll', frame)
            if cv2.waitKey(1) & 0xFF == ord(' '):
                cv2.imwrite('dice_roll.jpg', frame)
                dice_values = self.detect_dice('dice_roll.jpg')
                cap.release()
                cv2.destroyAllWindows()
                return dice_values
    
    def process_turn(self, dice_values):
        if not dice_values or len(dice_values) != 2:
            print("Error: Invalid dice roll. Please try again.")
            return

        total = sum(dice_values)
        print(f"Dice roll: {dice_values[0]} + {dice_values[1]} = {total}")

        if total in [2, 3]:
            print("Strike Out")
            self.outs += 1
        elif total == 4:
            print("Walk")
            self.advance_runners(1)
        elif total in [5, 6, 7]:
            print("Single")
            self.advance_runners(1)
        elif total in [8, 9]:
            print("Double")
            self.advance_runners(2)
        elif total == 10:
            print("Triple")
            self.advance_runners(3)
        elif total in [11, 12]:
            print("Home Run")
            self.advance_runners(4)

    def advance_runners(self, bases):
        runs = 0
        for i in range(3, 0, -1):
            if i + bases > 3:
                if self.bases[i-1]:
                    runs += 1
                    self.bases[i-1] = False
            else:
                self.bases[i+bases-1] = self.bases[i-1]
                self.bases[i-1] = False
        
        if bases == 4:  # Home run
            runs += 1  # Batter scores

        self.bases[bases-1] = True if bases < 4 else False
        self.score[self.current_team] += runs

    def play_inning(self):
        print(f"\nInning {self.inning}, {self.current_team} batting")
        self.outs = 0
        self.bases = [False, False, False]
        while self.outs < 3:
            input("Press Enter to roll the dice...")
            dice_values = self.capture_and_process_dice()
            self.process_turn(dice_values)
            self.display_game_state()
        print(f"End of {self.current_team}'s turn")
        self.current_team = "Home" if self.current_team == "Guest" else "Guest"

    def display_game_state(self):
        print(f"Score: Guest {self.score['Guest']} - Home {self.score['Home']}")
        print(f"Outs: {self.outs}")
        print(f"Bases: {'1' if self.bases[0] else '_'} {'2' if self.bases[1] else '_'} {'3' if self.bases[2] else '_'}")

    def play_game(self):
        while self.inning <= 9 or self.score['Guest'] == self.score['Home']:
            self.play_inning()
            if self.current_team == "Guest":
                self.inning += 1
        print("\nGame Over!")
        print(f"Final Score: Guest {self.score['Guest']} - Home {self.score['Home']}")
        winner = "Guest" if self.score['Guest'] > self.score['Home'] else "Home"
        print(f"{winner} wins!")

# Instantiate the game
game = BaseballGame()

@app.route('/')
def home():
    return render_template('index.html', game_state=game.display_game_state())

@app.route('/roll', methods=['POST'])
def roll_dice():
    dice_values = game.capture_and_process_dice()
    game.process_turn(dice_values)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
