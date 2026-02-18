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
        """Prepare features for ML model with enhanced rookie development modeling"""
        df = df.copy()
        
        # Encode categorical variables
        df['team_encoded'] = self.team_encoder.fit_transform(df['team'])
        df['position_encoded'] = self.position_encoder.fit_transform(df['position'])
        
        # Calculate value metrics
        df['price_per_point'] = df['price'] / (df['avg_score'] + 1)
        df['form_ratio'] = df['form_last_5'] / (df['avg_score'] + 1)
        
        # Enhanced age-based features for rookie development
        df['age_squared'] = df['age'] ** 2  # Capture non-linear age effects
        df['years_to_peak'] = np.abs(df['age'] - 26)  # Distance from peak age
        
        # Rookie and young player identification (key for development modeling)
        df['is_rookie'] = (df['age'] <= 20).astype(int)  # First/second year players
        df['is_young_developing'] = ((df['age'] > 20) & (df['age'] <= 23)).astype(int)  # Development years
        df['is_prime_age'] = ((df['age'] >= 24) & (df['age'] <= 28)).astype(int)  # Peak performance
        df['is_veteran'] = (df['age'] > 28).astype(int)  # Experienced players
        
        # Games experience features (important for rookie trajectory)
        df['experience_level'] = np.log1p(df['games_played'])  # Log transform for diminishing returns
        df['games_per_year'] = df['games_played'] / np.maximum(df['age'] - 17, 1)  # Availability rate
        
        # Draft pick features (lower draft pick = better, critical for rookies)
        df['is_top_10_pick'] = (df['draft_pick'] <= 10).astype(int)
        df['is_first_round_pick'] = (df['draft_pick'] <= 20).astype(int)
        df['elite_draft_pedigree'] = (df['draft_pick'] <= 5).astype(int)  # Top 5 picks - elite talent
        
        # Rookie development trajectory features
        # High draft picks who are young have huge upside
        df['rookie_upside'] = (
            df['is_rookie'] * df['draft_value'] * 2 +  # Rookies with good draft position
            df['is_young_developing'] * df['draft_value'] * 1.5  # Young players still developing
        )
        
        # Potential-based projections (critical for rookies getting better)
        df['potential_adjusted_score'] = df['avg_score'] * df['potential']
        df['growth_potential'] = np.maximum(0, (23 - df['age']) / 5) * df['draft_value']  # Years of growth left
        
        # For rookies/young players with limited games, boost score by potential
        df['projected_improvement'] = 0.0
        # Rookies (age <= 20) with top draft picks expected to improve significantly
        df.loc[df['is_rookie'] == 1, 'projected_improvement'] = df['draft_value'] * 15  # Up to 15 point improvement
        # Young developing players (21-23) still improving
        df.loc[df['is_young_developing'] == 1, 'projected_improvement'] = df['draft_value'] * 8  # Up to 8 point improvement
        
        # Combine current performance with projected improvement
        df['future_score_projection'] = df['avg_score'] + df['projected_improvement']
        
        # Injury impact (but less penalty for young players with no history)
        df['injury_risk'] = df['injury_history'] + df['injured_last_year'] * 2
        df['availability_score'] = df['games_last_3'] / 3.0  # 0-1 scale
        
        # Select features for model
        feature_cols = [
            # Age and development features
            'age', 'age_squared', 'years_to_peak', 'potential',
            'is_rookie', 'is_young_developing', 'is_prime_age', 'is_veteran',
            
            # Experience features
            'games_played', 'experience_level', 'games_per_year',
            
            # Draft pedigree (critical for rookie evaluation)
            'draft_pick', 'draft_value', 'is_top_10_pick', 'is_first_round_pick', 'elite_draft_pedigree',
            
            # Performance features
            'avg_disposals', 'avg_kicks', 'avg_handballs',
            'avg_marks', 'avg_tackles', 'avg_goals', 'avg_behinds', 'avg_hitouts',
            
            # Team and position
            'team_encoded', 'position_encoded',
            
            # Health and availability
            'injured_last_year', 'injury_history', 'injury_risk',
            'games_last_3', 'availability_score',
            
            # Form and value
            'form_last_5', 'price_per_point', 'form_ratio',
            
            # Potential and development (key for rookies)
            'potential_adjusted_score', 'rookie_upside', 'growth_potential',
            'projected_improvement', 'future_score_projection'
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
        """Calculate value scores with enhanced rookie development modeling"""
        df = df.copy()
        
        # Predict expected scores (includes rookie improvement projections)
        predicted_scores = self.predict_scores(df)
        df['predicted_score'] = predicted_scores
        
        # Calculate base value (points per $100k)
        df['value_score'] = (df['predicted_score'] / df['price']) * 100000
        
        # Risk adjustment based on injury history and availability
        df['risk_factor'] = 1 - (df['injury_history'] * 0.1)
        df['risk_factor'] = df['risk_factor'].clip(0.5, 1.0)
        
        # Additional penalty for injured last year
        df.loc[df['injured_last_year'] == 1, 'risk_factor'] *= 0.9
        
        # Enhanced upside factor for rookies and young players getting better
        df['upside_factor'] = 1.0
        
        # Rookies (age <= 20): Massive upside if high draft picks
        rookie_mask = df['age'] <= 20
        df.loc[rookie_mask, 'upside_factor'] = (
            1.0 + (df.loc[rookie_mask, 'potential'] - 1.0) * 1.5 +  # Potential boost
            df.loc[rookie_mask, 'draft_value'] * 0.3  # Draft pedigree boost
        )
        
        # Young developing players (21-23): Strong upside
        young_mask = (df['age'] > 20) & (df['age'] <= 23)
        df.loc[young_mask, 'upside_factor'] = (
            1.0 + (df.loc[young_mask, 'potential'] - 1.0) * 1.2 +  # Potential boost
            df.loc[young_mask, 'draft_value'] * 0.2  # Draft pedigree boost
        )
        
        # Elite draft picks (top 5) get extra boost - they're future stars
        elite_draft_mask = df['draft_pick'] <= 5
        df.loc[elite_draft_mask & (df['age'] <= 23), 'upside_factor'] *= 1.15
        
        # Breakout potential: Young players with limited games but good stats
        breakout_potential_mask = (
            (df['age'] <= 23) & 
            (df['games_played'] < 44) &  # Less than 2 full seasons
            (df['avg_score'] > 60)  # Already showing promise
        )
        df.loc[breakout_potential_mask, 'upside_factor'] *= 1.1
        
        # Adjusted value score with risk and upside
        # For overall rank, we prioritize total score, so upside matters more
        df['adjusted_value'] = df['value_score'] * df['risk_factor'] * df['upside_factor']
        
        # For overall rank optimization: Create score-focused metric
        # This prioritizes predicted score with rookie upside
        df['overall_rank_score'] = df['predicted_score'] * df['upside_factor'] * df['risk_factor']
        
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
