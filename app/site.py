import altair as alt
import streamlit as st
import pandas as pd
from service import (
    create_garden_tree_record,
    get_all_garden_records,
    update_garden_tree_record,
    delete_garden_tree_record,
    ServiceError,
)
from constants import DAYS_OF_THE_WEEK

st.set_page_config(layout="wide")

st.title("Аналитическая сводка сада Агафьи Алексеевны.")

with st.container():
    st.header(body="Создать новую запись")
    day_of_the_week: str = st.selectbox(label="День недели", options=DAYS_OF_THE_WEEK)
    name: str = st.text_input(label="Название дерева")
    fruits_num: float = st.number_input(label="Число фруктов", value=0)
    button = st.button(label="Сохранить")

    if button:
        try:
            create_garden_tree_record(
                day_of_the_week=day_of_the_week, name=name, fruits_num=fruits_num
            )
            st.success("Запись сохранена")
        except ServiceError as err:
            st.error(err.message)

    # Получение данных из БД
    data_frame_list = get_all_garden_records(order_by="day_of_the_week, name")
    pandas_dataframe = pd.DataFrame(data_frame_list)

    st.divider()

    if data_frame_list:

        # Фильтрация по таблице
        query = st.text_input("Фильтр")
        if query:
            pandas_dataframe = pandas_dataframe[
                pandas_dataframe.name.str.contains(query)
            ]

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
                    update_garden_tree_record(
                        filter_by_args={"id": record_id}, **update_kwargs
                    )

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

        altair_chart = (
            alt.Chart(pandas_dataframe)
            .mark_line()
            .encode(
                x=alt.X("day_of_the_week", sort=None).title("День недели"),
                y=alt.Y("fruits_num").title("Число фруктов"),
                color=alt.Color("name").title("Название дерева"),
            )
        )
        st.altair_chart(altair_chart, use_container_width=True)
