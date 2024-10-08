import altair as alt
import pandas as pd
import streamlit as st
from constants import COLUMNS_MAP, DAYS_OF_THE_WEEK
from service import (
    ServiceError,
    create_garden_tree_record,
    delete_garden_tree_record,
    get_all_garden_records,
    update_garden_tree_record,
)

st.title("Аналитическая сводка сада Агафьи Алексеевны")

with st.container():
    st.header(body="Создать новую запись")
    day_of_the_week: str = st.selectbox(label="День недели", options=DAYS_OF_THE_WEEK)
    name: str = st.text_input(label="Название дерева")
    fruits_num: float = st.number_input(label="Число фруктов", value=0)
    button = st.button(label="Сохранить")

    if button:
        try:
            create_garden_tree_record(day_of_the_week=day_of_the_week, name=name, fruits_num=fruits_num)
            st.success("Запись сохранена")
        except ServiceError as err:
            st.error(err.message)

with st.container():
    # Получение данных из БД
    data_frame_list = get_all_garden_records(order_by="day_of_the_week, name")
    pandas_dataframe = pd.DataFrame(data_frame_list)

    st.divider()

    if data_frame_list:

        # Фильтрация по таблице
        query = st.text_input("Фильтр")
        columns_filter = st.multiselect(
            "Какие столбцы использовать для фильтрации записей?",
            options=[
                "День недели",
                "Название дерева",
                "Число фруктов",
                "Температура °C",
                "ID (назначается автоматически)",
            ],
            default=["Название дерева"],
        )
        if query and columns_filter:
            columns_filter = [COLUMNS_MAP[i] for i in columns_filter]
            pandas_dataframe.query(
                # Переводим все столбцы в строки для поиска по значению
                " or ".join([f"{i}.astype('string').str.contains(@query)" for i in columns_filter]),
                inplace=True,
            )

        data_editor = st.data_editor(
            pandas_dataframe,
            column_config={
                "id": st.column_config.NumberColumn(
                    "ID (назначается автоматически)",
                    disabled=True,
                    width="small",
                ),
                "day_of_the_week": st.column_config.SelectboxColumn(
                    "День недели",
                    options=DAYS_OF_THE_WEEK,
                    width="medium",
                ),
                "name": st.column_config.TextColumn(
                    "Название дерева",
                    width="medium",
                ),
                "fruits_num": st.column_config.NumberColumn(
                    "Число фруктов",
                    width="medium",
                ),
                "temperature": st.column_config.NumberColumn(
                    "Температура °C",
                    width="medium",
                    disabled=True,
                ),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="data_editor",
        )

        # Запись в БД изменений таблицы
        try:
            commit_button = st.button("Сохранить изменения")

            if commit_button:
                edited_rows = st.session_state["data_editor"]["edited_rows"]
                for index, update_kwargs in edited_rows.items():
                    record_id = pandas_dataframe.iloc[index]["id"]
                    update_garden_tree_record(filter_by_args={"id": record_id}, **update_kwargs)

                added_rows = st.session_state["data_editor"]["added_rows"]
                for create_kwargs in added_rows:
                    # Чтобы не возникала ошибка при неполном вводе данных
                    if not create_kwargs or len(create_kwargs) < 3:
                        continue
                    create_garden_tree_record(**create_kwargs)

                deleted_rows = st.session_state["data_editor"]["deleted_rows"]
                for index in deleted_rows:
                    record_id = pandas_dataframe.iloc[index]["id"]
                    delete_garden_tree_record(filter_by_args={"id": record_id})

                st.rerun()

        except ServiceError as err:
            st.error(err.message)

        st.divider()

        fruits_by_day_line_chart = (
            alt.Chart(pandas_dataframe)
            .mark_line()
            .encode(
                x=alt.X("day_of_the_week", sort=None).title("День недели"),
                y=alt.Y("fruits_num").title("Число фруктов (шт.)"),
                color=alt.Color("name").title("Название дерева"),
            )
        )
        temperature_bar_chart = (
            alt
            # Убираем дупликаты температуры, чтобы не складывалась температура от разных деревьев
            # Считаем что температура зависит только от дня недели
            .Chart(pandas_dataframe.drop_duplicates("day_of_the_week"))
            .mark_bar(color="#dcdcdc")
            .encode(
                x=alt.X("day_of_the_week", sort=None).title("День недели"),
                y=alt.Y("temperature").title("Температура °C"),
            )
        )

        common_chart = (
            (temperature_bar_chart + fruits_by_day_line_chart)
            .resolve_scale(y="shared")
            .properties(width=600, height=600)
        )

        st.altair_chart(common_chart, use_container_width=True)
