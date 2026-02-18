"""
Machine Learning models for player performance prediction
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import config


class PlayerPerformancePredictor:
    """Predicts player performance using ML models"""
    
    def __init__(self):
        self.score_model = None
        self.price_model = None
        self.team_encoder = LabelEncoder()
        self.position_encoder = LabelEncoder()
        self.is_trained = False
        
    def prepare_features(self, df):
        """Prepare features for ML model"""
        df = df.copy()
        
        # Encode categorical variables
        df['team_encoded'] = self.team_encoder.fit_transform(df['team'])
        df['position_encoded'] = self.position_encoder.fit_transform(df['position'])
        
        # Calculate value metrics
        df['price_per_point'] = df['price'] / (df['avg_score'] + 1)
        df['form_ratio'] = df['form_last_5'] / (df['avg_score'] + 1)
        
        # Age-based features
        df['age_squared'] = df['age'] ** 2  # Capture non-linear age effects
        df['years_to_peak'] = np.abs(df['age'] - 26)  # Distance from peak age
        
        # Draft pick features (lower draft pick = better)
        df['is_top_10_pick'] = (df['draft_pick'] <= 10).astype(int)
        df['is_first_round_pick'] = (df['draft_pick'] <= 20).astype(int)
        
        # Injury impact
        df['injury_risk'] = df['injury_history'] + df['injured_last_year'] * 2
        df['availability_score'] = df['games_last_3'] / 3.0  # 0-1 scale
        
        # Potential adjusted performance
        df['potential_adjusted_score'] = df['avg_score'] * df['potential']
        
        # Select features
        feature_cols = [
            'age', 'age_squared', 'years_to_peak', 'potential',
            'games_played', 'avg_disposals', 'avg_kicks', 'avg_handballs',
            'avg_marks', 'avg_tackles', 'avg_goals', 'avg_behinds', 'avg_hitouts',
            'team_encoded', 'position_encoded', 
            'draft_pick', 'draft_value', 'is_top_10_pick', 'is_first_round_pick',
            'injured_last_year', 'injury_history', 'injury_risk',
            'games_last_3', 'availability_score',
            'form_last_5', 'price_per_point', 'form_ratio',
            'potential_adjusted_score'
        ]
        
        X = df[feature_cols]
        return X, df
    
    def train_score_predictor(self, df):
        """Train model to predict player scores"""
        print("Training score prediction model...")
        
        X, df = self.prepare_features(df)
        y = df['avg_score']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=config.MODEL_CONFIG['test_size'],
            random_state=config.MODEL_CONFIG['random_state']
        )
        
        # Train ensemble model
        self.score_model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            random_state=config.MODEL_CONFIG['random_state']
        )
        
        self.score_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.score_model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        
        print(f"Score Model Performance:")
        print(f"  RMSE: {rmse:.2f}")
        print(f"  MAE: {mae:.2f}")
        print(f"  R2 Score: {r2:.4f}")
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.score_model, X, y, cv=config.MODEL_CONFIG['cv_folds'],
            scoring='neg_mean_squared_error'
        )
        print(f"  CV RMSE: {np.sqrt(-cv_scores.mean()):.2f} (+/- {np.sqrt(cv_scores.std()):.2f})")
        
        return self.score_model
    
    def predict_scores(self, df):
        """Predict scores for players"""
        if self.score_model is None:
            raise ValueError("Model not trained. Call train_score_predictor() first.")
        
        X, _ = self.prepare_features(df)
        predictions = self.score_model.predict(X)
        return predictions
    
    def calculate_value_scores(self, df):
        """Calculate value scores (predicted points per $1000 spent)"""
        df = df.copy()
        
        # Predict expected scores
        predicted_scores = self.predict_scores(df)
        df['predicted_score'] = predicted_scores
        
        # Calculate value (points per $100k)
        df['value_score'] = (df['predicted_score'] / df['price']) * 100000
        
        # Risk adjustment based on injury history and games played
        df['risk_factor'] = 1 - (df['injury_history'] * 0.1)
        df['risk_factor'] = df['risk_factor'].clip(0.5, 1.0)
        
        # Additional penalty for injured last year
        df.loc[df['injured_last_year'] == 1, 'risk_factor'] *= 0.9
        
        # Potential bonus for young players (upside)
        df['upside_factor'] = 1.0
        df.loc[df['age'] < 23, 'upside_factor'] = df['potential']
        
        # Adjusted value score with risk and upside
        df['adjusted_value'] = df['value_score'] * df['risk_factor'] * df['upside_factor']
        
        return df
    
    def save_model(self, filepath='model.pkl'):
        """Save trained model"""
        if self.score_model is None:
            raise ValueError("No model to save")
        
        model_data = {
            'score_model': self.score_model,
            'team_encoder': self.team_encoder,
            'position_encoder': self.position_encoder
        }
        joblib.dump(model_data, filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath='model.pkl'):
        """Load trained model"""
        model_data = joblib.load(filepath)
        self.score_model = model_data['score_model']
        self.team_encoder = model_data['team_encoder']
        self.position_encoder = model_data['position_encoder']
        self.is_trained = True
        print(f"Model loaded from {filepath}")
