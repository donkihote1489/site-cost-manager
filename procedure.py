def procedure_flow_view(site, year, month, cost_type):
    key = f"{site}_{year}_{month}_{cost_type}"

    if "절차상태" not in st.session_state:
        st.session_state.절차상태 = load_state_from_file()

    if key not in st.session_state.절차상태:
        steps = get_procedure_flow()[cost_type]
        st.session_state.절차상태[key] = {
            "current_step": 1,
            "status": {label: "진행중" for label, _ in steps},
            "amounts": {},
            "total_steps": len(steps)
        }

    state = st.session_state.절차상태[key]
    steps = get_procedure_flow()[cost_type]

    st.subheader(f"📌 비용유형: {cost_type}")   
    st.header("📋 절차 진행 현황")
    current_index = state["current_step"] - 1

    if current_index >= len(steps):
        st.success("🎉 모든 단계가 완료되었습니다.")
        return

    current_step, 담당부서 = steps[current_index]
    step_label = f"{current_index+1}. {current_step}"
    st.subheader(f"📍 현재 단계: {step_label}")
    st.markdown(f"담당 부서: `{담당부서}`")

    my_role = st.session_state.get("role", "")
    is_authorized = (my_role == 담당부서)

    if is_authorized:
        상태 = st.radio("진행 상태", ["진행중", "완료"],
                        index=0 if state["status"][current_step] == "진행중" else 1)
        state["status"][current_step] = 상태

        update_step_status(
            site=site,
            year=year,
            month=month,
            cost_type=cost_type,
            step_no=state["current_step"],
            상태=상태
        )

        cost_key = (cost_type, state["current_step"])
        if cost_key in COST_INPUT_CONDITIONS:
            label = COST_INPUT_CONDITIONS[cost_key]
            current_value = state["amounts"].get(label, 0)
            입력값 = st.number_input(f"💰 {label} 입력", min_value=0, step=100000, value=current_value)

            if st.button(f"💾 {label} 저장"):
                state["amounts"][label] = 입력값

                update_step_status(
                    site=site,
                    year=year,
                    month=month,
                    cost_type=cost_type,
                    step_no=state["current_step"],
                    상태=상태,
                    금액컬럼=label,
                    금액=입력값
                )

                save_state_to_file()
                st.success(f"✅ {label}이 DB에 저장되었습니다.")
                st.rerun()

            if label in state["amounts"]:
                st.info(f"💾 저장된 {label}: {state['amounts'][label]:,}원")
            else:
                st.warning(f"❗ 아직 {label}이 저장되지 않았습니다.")

        save_state_to_file()
    else:
        st.warning("⚠️ 이 단계는 귀하의 담당 부서가 아닙니다. 수정 권한이 없습니다.")

    # 다음 단계로 이동
    if state["status"][current_step] == "완료":
        cost_key = (cost_type, state["current_step"])
        if cost_key in COST_INPUT_CONDITIONS:
            label = COST_INPUT_CONDITIONS[cost_key]
            if label not in state["amounts"]:
                st.warning(f"⚠️ {label}을 저장한 뒤에 다음 단계로 이동할 수 있습니다.")
                return

        if st.button("다음 단계로 이동"):
            if state["current_step"] < state["total_steps"]:
                state["current_step"] += 1
                save_state_to_file()
                st.rerun()
            else:
                st.success("🎉 모든 단계가 완료되었습니다.")
                st.rerun()
    else:
        st.button("다음 단계로 이동", disabled=True)
