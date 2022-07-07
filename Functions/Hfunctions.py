### Imports
import pandas as pd
###-

###Class definition
class help_functions():
    #load data
    def data_load( path ):
        data = pd.read_csv( path + 'kc_house_data.csv' )
        return data

    #data preparation   
    def business_op_create( df ):
        df['date']  = pd.to_datetime( df['date'] )
        df['month'] = df['date'].dt.month
        df['year']  = df['date'].dt.year

        #season set
        for i in df.index:
            if ( df.loc[i, 'month']  < 3 ) | ( df.loc[i, 'month'] == 12 ):
                 df.loc[i, 'season'] = 'Winter'
            elif df.loc[i, 'month']  < 6:
                 df.loc[i, 'season'] = 'Spring'
            elif df.loc[i, 'month']  < 9:
                 df.loc[i, 'season'] = 'Summer'
            else:
                 df.loc[i, 'season'] = 'Autumn'            

        #average by zipcode
        aux = df[['zipcode', 'price']].groupby('zipcode').mean().reset_index()
        aux.rename( columns = {'price':'average_price'}, inplace=True )
        aux = pd.merge( aux, df, how='inner', on='zipcode' )

        #median by zipcode
        aux1 = df[['zipcode', 'price']].groupby('zipcode').median().reset_index()
        aux1.rename( columns={'price': 'median_price'}, inplace=True )
        aux  = pd.merge( aux, aux1, how='inner', on='zipcode' )
        df   = pd.concat( [df,aux] )

        #square foot price
        df['sq_foot_price'] = df[['price','sqft_lot']].apply( lambda x: x['price'] / x['sqft_lot'], axis=1 )

        #indication atribute (30% of median price)
        df['status']        = df[['price', 'median_price', 'condition']].apply( lambda x : 'buy' if ( x['price'] < (x['median_price'] * 0.7) ) & (x['condition'] > 3 ) else 'not_buy', axis=1 )

        #create Dataframe of business opportunities
        business_opportunities = df.loc[
            df.status == 'buy',
            ['id', 'condition', 'date', 'zipcode', 'lat', 'long', 'price', 'average_price',
             'median_price', 'bedrooms', 'bathrooms', 'sqft_living', 'sqft_lot', 'floors' , 
             'waterfront', 'view', 'yr_built', 'yr_renovated', 'sq_foot_price']
        ].reset_index( drop=True )

        #difference between the average price by region and the price of the property  
        business_opportunities['average_percentage_difference'] = business_opportunities[['price','average_price']].apply( ( lambda x: ( x['average_price'] - x['price'] ) / x['average_price'] * 100 ), axis=1 )
        business_opportunities['median_percentage_difference']  = business_opportunities[['price','median_price']].apply ( ( lambda x: ( x['median_price'] - x['price'] ) / x['median_price'] * 100 ), axis=1 )

        #season of the year with the highest averages for sale by region
        df_temp   = df[['price', 'season', 'zipcode']].groupby( ['zipcode', 'season'] ).mean().reset_index()
        season    = []
        for z in df_temp.zipcode.unique():
            price = df_temp.loc[df_temp.price == df_temp[df_temp.zipcode == z].price.max()].season.values[0]
            season.append([z,price])
        df_temp   = pd.DataFrame(season, columns=['zipcode', 'highest_season_sale'])
        #concat dataframes: season of the year with the highest averages for sale | business opportunities
        business_opportunities = pd.merge(business_opportunities, df_temp, how= 'left', on='zipcode').reset_index(drop=True)

        ###suggested sale price calculation (  )
        #Calculado apartir da classificação da diferença do preço para a média e o alvo de 40% de roi
        business_opportunities['suggested_price'] = business_opportunities[['price', 'median_percentage_difference']].apply( lambda x: x['price'] + ( ( x['price'] * ( x['median_percentage_difference'] + 7 ) ) / 100 ), axis=1 )

        ###expected profit
        business_opportunities['expected_profit']       = business_opportunities[['price', 'suggested_price']].apply( lambda x: x['suggested_price'] - x['price'], axis=1 )
        business_opportunities.sort_values('expected_profit', inplace=True)
        business_opportunities['cumulative_investment'] = business_opportunities[['price']].cumsum()
        business_opportunities['cumulative_profit'] = business_opportunities[['expected_profit']].cumsum()
        business_opportunities.reset_index(drop=True, inplace=True)
        ci_min    = 1
        ci_max    = int( business_opportunities['cumulative_investment'].max() / 1000000 )
        ci_median = int( business_opportunities['cumulative_investment'].median() / 1000000 )

        return business_opportunities, ci_min, ci_median, ci_max
###-    