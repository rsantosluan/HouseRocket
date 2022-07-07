### Imports

##proprietary libraries
from Functions.Hfunctions import help_functions as hf

##plot
#maps
import folium
import geopandas
from   streamlit_folium import folium_static
from folium.plugins     import MarkerCluster
from urllib.error       import HTTPError
#charts
import plotly.express as px

##deploy
import streamlit as st

###-

### Page congif

#page layout
st.set_page_config( layout= 'wide' )
#data upload to cache
@st.cache( allow_output_mutation=True )
def nt():
    return None
#load data
df = hf.data_load( 'data/' )

###-

### Functions

#Descriptive data analysis
def descriptive_data ( df ):
    c1,c2 = st.columns( [2,1] )
    
    ##Checkboxes
    cols = ['price']
    c2.markdown( "--"*30 )
    be = c2.checkbox( 'Bedrooms', value = True )
    ba = c2.checkbox( 'Bathrooms', value = True )
    li = c2.checkbox( 'Sqft_living', value = True )
    lo = c2.checkbox( 'Sqft_lot', value = True )
    fl = c2.checkbox( 'Floors', value = True )
    co = c2.checkbox( 'Condition', value = True )
    c2.markdown( "--"*30 )

    if be:
        cols.append( 'bedrooms' )
    if ba:
        cols.append( 'bathrooms' )
    if li:    
        cols.append( 'sqft_living' )
    if lo:    
        cols.append( 'sqft_lot' )
    if fl:    
        cols.append( 'floors' )
    if co:    
        cols.append( 'condition' )

    ##General Analysis
    temp = df[cols].describe().T
    temp.drop(columns=['count'],inplace=True)
    #chart
    c1.markdown( 'Análise geral' )
    c1.dataframe( temp )

    c1,c2,c3 = st.columns( [1,1,1] )

    ##Chart
    chart = c1.checkbox( 'Plotar gráfico de regiões com maior média de preço.', value = False )
    if chart:
        density_price         = df[['price','zipcode']].groupby('zipcode').mean().reset_index()
        density_price.columns = ['ZIP','Preço'] 
        temp        = density_price.sort_values('Preço', ascending=False).copy()
        temp['ZIP'] = temp['ZIP'].apply( lambda x : str( x ) )
        fig = px.bar( temp.head(5), x='ZIP', y='Preço' )
        fig.update_layout( title='Regiões com maior média de preço' )
        st.plotly_chart( fig, use_container_width=True )      

    ##Map
    map = c2.checkbox( 'Plotar mapa de calor referente a preços por região.', value = False )
    if map:
        #get geofile
        url = 'https://opendata.arcgis.com/datasets/83fc2e72903343aabff6de8cb445b81c_2.geojson'
        #url = 'https://services2.arcgis.com/I7NQBinfvOmxQbXs/arcgis/rest/services/sps_geo_zone_ES_2021_2022/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson'
        try:
            geofile = geopandas.read_file( url )
            #grouping
            density_price         = df[['price','zipcode']].groupby('zipcode').mean().reset_index().copy()
            density_price.columns = ['ZIP','Preço'] 
            geofile               = geofile[geofile['ZIP'].isin( density_price.ZIP.tolist() )]
            #map
            region_price_map   = folium.Map(
            location           = [df.lat.median(), df.long.median()],
            default_zoom_start = 2,
            png_enabled        = True
            )
            region_price_map.choropleth(
                data         = density_price,
                name         = 'choropleth',
                geo_data     = geofile,
                columns      = ['ZIP','Preço'],
                key_on       = 'feature.properties.ZIP',
                fill_color   ='YlOrRd',
                fill_opacity = 0.7,
                line_opacity = 0.3,
                legend_name  = 'Mean Price',
            )
            ###ploting
            #map
            st.subheader('Média de preço por região ( Zipcode )')
            folium_static( region_price_map )
        except HTTPError as error_mensage:
            st.warning('⚠️ Desculpe, o Servidor contendo informações essenciais para o plot deste mapa está passando por Instabilidades. Erro: {}'.format( error_mensage ))  
    
    ##Average price dataframe by region
    cb_avg_price = c3.checkbox( 'Mostrar tabela geral de média de preços por região. ', value = False )
    if cb_avg_price:
        temp = df[[ 'price', 'zipcode']].groupby('zipcode').mean().reset_index()
        temp.rename( columns = {'zipcode' : 'Código Postal','price' : 'Preço'}, inplace=True )
        st.dataframe( temp )


    return None 

#Business oportunities analysis 
def b_oportunities( df ):
    df_bo, ci_min, ci_median, ci_max = hf.business_op_create( df )
    
    ### ROI Analisis
    qtde = st.slider( 'Selecione o range (em milhões de dólares) para investimento ', ci_min, ci_max, ci_median  )
    ### renovated filter
    renovated = st.checkbox( 'Filtrar apenas por casas que ainda não foram reformadas' )


    
    ### Filter data
    if renovated:
        df_bof = df_bo.loc[(df_bo.cumulative_investment <= qtde * 1000000) & ( df_bo.yr_renovated == 0 ) , 
        ['id', 'lat', 'long','yr_renovated', 'price', 'sq_foot_price', 'highest_season_sale', 'suggested_price', 'expected_profit', 'cumulative_investment', 'cumulative_profit','zipcode']].copy()
    else:    
        df_bof = df_bo.loc[df_bo.cumulative_investment <= qtde * 1000000, 
        ['id', 'lat', 'long','yr_renovated', 'price', 'sq_foot_price', 'highest_season_sale', 'suggested_price', 'expected_profit', 'cumulative_investment', 'cumulative_profit','zipcode']].copy()

    #rescale Num
    if df_bof.cumulative_profit.max() > 1000000:
        cum_profit = str( round( df_bof.cumulative_profit.max() / 1000000 ) ) + 'Milhões'
    else:
        cum_profit = str( round( df_bof.cumulative_profit.max()) )
    #percentage profit
    perc_profit    = ( ( df_bof.cumulative_investment.max() + df_bof.cumulative_profit.max() ) -  df_bof.cumulative_investment.max() ) / df_bof.cumulative_investment.max() *100 
    count_h        = ( df_bof.id.count() )

    ###general metrics dataframe
    st.metric( 'Retorno Sobre Investimento','Retorno líquido esperado de $ {}'.format( cum_profit ) ,'{:.0f} % de ROI'.format( perc_profit ) )  
    
    c1,c2 = st.columns( [3.3,1] )
    #rename columns
    bo_temp = df_bof[['id', 'price', 'suggested_price', 'expected_profit','yr_renovated', 'sq_foot_price', 'highest_season_sale', 'cumulative_investment', 'cumulative_profit']]
    bo_temp.rename(
        columns = {'id' :'ID', 'price' : 'Preço', 'suggested_price' : 'Preço Sugerido', 'expected_profit' : 'Lucro Esperado',
        'yr_renovated': 'Ano em que foi reformada', 'sq_foot_price' : 'Preço do pé quadrado', 'highest_season_sale' : 'Melhor estação para venda',
        'cumulative_investment' : 'Investimento Acumulado', 'cumulative_profit' : 'Lucro esperado acumulado'}, inplace=True
    )
    ##Checkboxes    
    cols_bo = ['ID', 'Preço', 'Preço Sugerido', 'Lucro Esperado']
    
    c2.markdown( "--"*30 )
    sfp = c2.checkbox( 'Preço do pé quadrado', value = True )
    hss = c2.checkbox( 'Melhor estação para venda', value = True )
    ci = c2.checkbox( 'Investimento Acumulado', value = True )
    cp = c2.checkbox( 'Retorno Acumulado', value = True )
    if sfp:
        cols_bo.append( 'Preço do pé quadrado' )
    if hss:
        cols_bo.append( 'Melhor estação para venda' )
    if ci:    
        cols_bo.append( 'Investimento Acumulado' )
    if cp:    
        cols_bo.append( 'Lucro esperado acumulado' )
    
    c2.markdown( "--"*30 )
    c1.dataframe( bo_temp[cols_bo] )
    c2.info('{} imóveis retornados'.format( count_h ))

    ###Map Plot
    density_map = folium.Map(
        location = [df_bof['lat'].mean(), df_bof['long'].mean()],
        width='100%',
        height= '100%',
        default_zoom_start = 15,
    )
                                        
    marker_cluster = MarkerCluster().add_to( density_map )

    for name, row in df_bof.iterrows():
        folium.Marker( [row['lat'], row['long']], 
            popup =  
                'Id: {0} \n  |Zipcode: {1} \n |Preço sugerido: {2:.2f} \n |Lucro : {3:.2f}'. format( 
                    row['id'],
                    row['zipcode'], 
                    row['price'],
                    row['expected_profit'],
                )).add_to(marker_cluster)
        
    
    folium_static(density_map)
    return None


###-

### Header
c1,c2 = st.columns( [1,10] )
c1.image( 'img/HR.png')

c2.header( '| Painel de análises e detecção de oportunidades de negócio HR |' )
st.markdown( '---'*30 )

###-

### Main

if __name__ == '__main__': 

    st.subheader( 'Visão Geral dos dados do portfólio' )
    descriptive_data( df )
    st.markdown('-'*30)

    st.subheader( 'Visão geral das propostas de oportunidades de negócio' )
    b_oportunities( df )

    st.markdown( '--' * 30 )
    
    ### Final considerations    
    st.subheader ( 'Considerações Finais' )    
    st.write(
        'No decorrer do EDA (Análise Estatística dos dados), foram levantadas e testadas diversas hipóteses.\
        Em suma, foram obtidas informações valiosas que regeram essa primeira etapa e deram uma base sólida para a proposta de um novo cícolo. Dentre elas, destacam-se:'        
    )
    ##h1
    st.markdown( '**1-** Imóveis com Vista para água, tem em média uma inflação de valores de 212,64% quando comparadas com os que não possuem.')
    st.caption( '**-** Fato esse que, devido as regras de negócio acordadas em primeiro cícolo, inviabilizou o retorno de imóveis com vista para a água como sugestão de compra mas, \
                evidencia um bom parâmetro para análises posteriores.' )
    ##h2
    st.markdown( '**2-** Imóveis que passam por reforma tem em média uma inflação de valores de 43,37% quando comparados com os que não passam.')
    st.caption( '**-** Fato esse que, levou a criação do filtro localizado acima da tabela de indicações pois \
                evidencia um bom parâmetro para análises do CFO podendo ser incorporado em modelos nos cícolos futuros.' )   
    
    st.subheader( '_Contextualização_' ) 
    st.markdown( 'Necessidade: ' )                     
    st.caption( 'Relatório que auxilie o CEO na tomada de decisão para atingir a meta de Retorno sobre Investimentos (ROI) de 40%. ' )
    st.markdown( 'Causas: ' )                     
    st.caption( 'A quantidade elevada de imóveis contidas no portifólio, atrapalha muito na obtenção de padrões e se torna contra \
                intuitiva podendo levar a decisões precipitadas e/ou perda de bons negócios.' )
    st.markdown( 'Proposta de Solução: ' )                   
    st.caption( 'Por meio de análises estatísticas serão elencados possíveis bons negócios com base nos atributos disponibilizados no\
                portfólio fornecido pelo CEO. Elencando casas que foram anunciadas com preço abaixo de 30% do valor médio por região, \
                estejam em ótimo estado de conservação além de analisar o período do ano em que cada região apresenta maior média de   \
                preços para definição do momento ideal para revenda do imóvel. Para calcular o valor sugerido de venda, colocaremos uma \
                margem de mais 7% sobre o valor mediano dos imóveis da região.' )
    
###-

### Baseboard
c = st.container()
c.markdown( '--'*30 )

c1,c2,c3 = st.columns( [1.3,3,15] )
c1.caption( 'Contatos: ' )
c2.caption( 
    '[Linkedin](https://www.linkedin.com/in/luan-rs/) | | \
    [GitHub](https://github.com/rsantosluan) '
 )


###-


